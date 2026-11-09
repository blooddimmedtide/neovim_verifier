// Full-correctness harnesses for the .spl reader helpers. The spec is written from the
// .spl format (runtime/doc/spell.txt, "<regionname>", "<charflagslen>" ...: counts are
// MSB-first unsigned bytes) and the functions' own comments, not from their code.
// Every input is nondeterministic: file length 0..N (N = SPL_N) and every byte.
#include SPELLFILE_C
#ifndef SPL_N
#define SPL_N 20
#endif
size_t nondet_size(void); int nondet_int(void); unsigned char nondet_uchar(void);

static unsigned char buf[SPL_N];
static FILE mkfile(void) {
  for (int i = 0; i < SPL_N; i++) buf[i] = nondet_uchar();
  FILE f; f.len = nondet_size(); __CPROVER_assume(f.len <= SPL_N);
  // exact-size object: reads past len hit the end of an allocation of len bytes
  unsigned char *d = malloc(f.len); memcpy(d, buf, f.len);
  f.data = d; f.pos = 0; f.eof = false; return f;
}

// spell_check_magic_string: 0 iff the file starts with the 8 bytes "VIMspell",
// SP_TRUNCERROR if it holds fewer than 8 bytes, SP_FORMERROR otherwise.
static int spec_magic(size_t len) {
  if (len < 8) return SP_TRUNCERROR;
  const char m[8] = {'V','I','M','s','p','e','l','l'};
  for (int i = 0; i < 8; i++) if (buf[i] != (unsigned char)m[i]) return SP_FORMERROR;
  return 0;
}
void h_magic(void) {
  FILE f = mkfile();
  int r = spell_check_magic_string(&f);
  __CPROVER_assert(r == spec_magic(f.len), "magic: result matches spec");
  __CPROVER_assert(f.pos == (f.len < 8 ? f.len : 8), "magic: consumes exactly the magic");
  free((void *)f.data);
}

// read_cnt_string(fd, k, &cnt), k in {1, 2} (the only widths spellfile.c uses):
// fewer than k bytes -> NULL, cnt = SP_TRUNCERROR. Count n = MSB-first value of the k bytes.
// n == 0 -> NULL, cnt = 0. Fewer than n bytes after the count -> NULL, cnt = SP_OTHERERROR
// (the function's comment: SP_*ERROR "when there is an error"; read_string reports a short
// read as failure without distinguishing truncation; recorded in CLAIM.md).
// Otherwise a fresh NUL-terminated copy of the next n bytes, cnt = n, n+k bytes consumed.
void h_cnt_string(void) {
  FILE f = mkfile();
  int k = nondet_int(); __CPROVER_assume(k == 1 || k == 2);
#ifdef CNT_K1
  __CPROVER_assume(k == 1);  // k = 1 run: SPL_N = 257 covers every count 0..255
#endif
  int cnt = 12345;
  char *s = read_cnt_string(&f, k, &cnt);
  if (f.len < (size_t)k) {
    __CPROVER_assert(s == NULL && cnt == SP_TRUNCERROR, "cnt: short count -> TRUNCERROR");
    free((void *)f.data); return;
  }
  unsigned n = k == 1 ? buf[0] : ((unsigned)buf[0] << 8) | buf[1];
  if (n == 0) {
    __CPROVER_assert(s == NULL && cnt == 0 && f.pos == (size_t)k, "cnt: zero -> NULL, 0");
  } else if (f.len - k < n) {
    __CPROVER_assert(s == NULL && cnt == SP_OTHERERROR, "cnt: short body -> OTHERERROR");
  } else {
    __CPROVER_assert(s != NULL && cnt == (int)n && f.pos == k + n, "cnt: ok result");
    __CPROVER_assert(__CPROVER_r_ok(s, n + 1), "cnt: n+1 bytes allocated");
    for (unsigned i = 0; i < n; i++) __CPROVER_assert(s[i] == (char)buf[k + i], "cnt: bytes copied");
    __CPROVER_assert(s[n] == NUL, "cnt: NUL terminated");
    free(s);
  }
  free((void *)f.data);
}

// read_region_section(fd, lp, len), 0 <= len (caller rejects negative get4c lengths):
// len > 16 -> SP_FORMERROR; fewer than len bytes -> SP_TRUNCERROR; a NUL among them ->
// SP_FORMERROR; otherwise sl_regions = those bytes + NUL and 0.
void h_region(void) {
  FILE f = mkfile();
  slang_T *lp = malloc(sizeof(slang_T));
  int len = nondet_int(); __CPROVER_assume(len >= 0);
  int r = read_region_section(&f, lp, len);
  free((void *)f.data);
  if (len > MAXREGIONS * 2) { __CPROVER_assert(r == SP_FORMERROR && f.pos == 0, "region: too long"); free(lp); return; }
  if (f.len < (size_t)len) { __CPROVER_assert(r == SP_TRUNCERROR, "region: truncated"); free(lp); return; }
  bool nul = false;
  for (int i = 0; i < len; i++) if (buf[i] == 0) nul = true;
  if (nul) { __CPROVER_assert(r == SP_FORMERROR, "region: NUL byte"); free(lp); return; }
  __CPROVER_assert(r == 0 && f.pos == (size_t)len, "region: ok");
  for (int i = 0; i < len; i++) __CPROVER_assert(lp->sl_regions[i] == (char)buf[i], "region: bytes");
  __CPROVER_assert(lp->sl_regions[len] == NUL, "region: NUL terminated");
  free(lp);
}
