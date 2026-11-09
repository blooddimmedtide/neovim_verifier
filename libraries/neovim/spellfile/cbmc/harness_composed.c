// read_cnt_string for EVERY file length and count (k in {1, 2}), composed with read_string's
// contract, which wp/run_wp.sh proves with Frama-C WP for every cnt. Only read_string is
// replaced (READ_STRING_CONTRACT); the count loop is upstream code, sha256 pinned.
#define READ_STRING_CONTRACT 1
#include SPELLFILE_C
size_t nondet_size(void); int nondet_int(void);

void h_cnt_string_all(void) {
  FILE f; f.len = nondet_size(); __CPROVER_assume(f.len <= 70000);
  unsigned char *d = malloc(f.len); f.data = d; f.pos = 0; f.eof = false;
  int k = nondet_int(); __CPROVER_assume(k == 1 || k == 2);
  int cnt = 12345;
  size_t j = nondet_size(); ghost_j = j;   // any one byte index: covers all bytes
  char *s = read_cnt_string(&f, k, &cnt);
  if (f.len < (size_t)k) {
    __CPROVER_assert(s == NULL && cnt == SP_TRUNCERROR, "cnt: short count -> TRUNCERROR");
  } else {
    unsigned n = k == 1 ? d[0] : ((unsigned)d[0] << 8) | d[1];
    if (n == 0) {
      __CPROVER_assert(s == NULL && cnt == 0 && f.pos == (size_t)k, "cnt: zero -> NULL, 0");
    } else if (f.len - k < n) {
      __CPROVER_assert(s == NULL && cnt == SP_OTHERERROR, "cnt: short body -> OTHERERROR");
    } else {
      __CPROVER_assert(s != NULL && cnt == (int)n && f.pos == k + n, "cnt: ok result");
      __CPROVER_assert(__CPROVER_r_ok(s, n + 1), "cnt: n+1 bytes allocated");
      __CPROVER_assert(j >= n || s[j] == (char)d[k + j], "cnt: bytes copied");
      __CPROVER_assert(s[n] == NUL, "cnt: NUL terminated");
      free(s);
    }
  }
  free(d);
}
