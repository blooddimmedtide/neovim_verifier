// CBMC proofs for the functions of src/xdiff/xutils.c that have no loop over unbounded
// data (the others are proved with Frama-C WP in ../wp/). Every input in the stated range.
// The spec of each harness is written from what the function is for (its name, its comment,
// how xdiff uses it and git's documentation), not from its code. See ../CLAIM.md.
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>
long nondet_long(void);
int nondet_int(void);
unsigned nondet_unsigned(void);
size_t nondet_size(void);
char nondet_char(void);
#include XUTILS_C   // verbatim src/xdiff/xutils.c; memory.h (the xmalloc model) comes with it

#define MAX_OBJ ((size_t)1 << 50)

// ---- reference: decimal text of a long, written forwards (the code writes backwards)
static int ref_dec(char *o, long v) {
  unsigned long u = v < 0 ? 0UL - (unsigned long)v : (unsigned long)v, p = 1;
  int k = 0;
  while (u / p >= 10) p *= 10;
  if (v < 0) o[k++] = '-';
  for (; p; p /= 10) o[k++] = (char)('0' + (u / p) % 10);
  o[k] = 0;
  return k;
}

// xdl_bogosqrt: "integer square root approximation": 2^ceil(b/2) where b is the bit
// length of n (so the result r satisfies r*r/4 <= n < r*r), and 1 for n <= 0.
void h_bogosqrt(void) {
  long n = nondet_long();
  long want = n <= 0 ? 1 : 1L << ((64 - __builtin_clzl((unsigned long)n) + 1) / 2);
  long got = xdl_bogosqrt(n);
  __CPROVER_assert(got == want, "2^ceil(bits(n)/2)");
  if (n > 0) __CPROVER_assert((unsigned long)got * got / 4 <= n && (__int128)got * got > n, "r*r/4 <= n < r*r");
}

// xdl_hashbits: the number of bits of a hash table with at least size slots: the smallest
// b >= 1 with 2^b >= size (32 for sizes above 2^31).
void h_hashbits(void) {
  unsigned size = nondet_unsigned();
  unsigned want = size <= 1 ? 1 : 32 - __builtin_clz(size - 1);
  unsigned got = xdl_hashbits(size);
  __CPROVER_assert(got == want, "smallest b >= 1 with 2^b >= size");
  __CPROVER_assert(got >= 1 && got <= 32 && (got == 32 || (1ULL << got) >= size), "table fits");
}

// xdl_num_out: writes the decimal text of val and a NUL to out, returns the text length.
// out has room for the longest text (20 characters and the NUL); nothing after the NUL
// is written.
void h_num_out(void) {
  long v = nondet_long();
  char want[24];
  int n = ref_dec(want, v);
  char *out = __CPROVER_allocate(21, 0);
  char before[21];
  for (int i = 0; i < 21; i++) before[i] = out[i];
  int got = xdl_num_out(out, v);
  __CPROVER_assert(got == n, "length");
  int j = nondet_int();
  __CPROVER_assume(0 <= j && j < 21);
  if (j <= n) __CPROVER_assert(out[j] == want[j], "decimal text and NUL");
  else __CPROVER_assert(out[j] == before[j], "nothing written after the NUL");
}

// ---- callbacks: record what the code passes and return a nondeterministic result
static int g_calls, g_ret, g_n; static void *g_priv;
static char *g_ptr[3]; static long g_size[3];
static int out_line(void *priv, mmbuffer_t *mb, int n) {
  g_calls++; g_priv = priv; g_n = n;
  __CPROVER_assert(n >= 1 && n <= 3 && __CPROVER_r_ok(mb, n * sizeof *mb), "mb readable");
  for (int i = 0; i < n; i++) { g_ptr[i] = mb[i].ptr; g_size[i] = mb[i].size; }
  return g_ret;
}

// xdl_emit_diffrec: passes one line to out_line as the buffers {pre, rec} and, when the
// line does not end with '\n', the marker "\n\\ No newline at end of file\n" (git's text);
// returns -1 when out_line fails (< 0), else 0. Sizes fit in int: mmbuffer_t.size is int
// and every record lies in an mmfile_t, whose size is int.
void h_emit_diffrec(void) {
  long size = nondet_long(), psize = nondet_long();
  __CPROVER_assume(0 <= size && size <= INT_MAX && 0 <= psize && psize <= INT_MAX);
  char *rec = __CPROVER_allocate(size, 0), *pre = __CPROVER_allocate(psize, 0);
  xdemitcb_t ecb; ecb.priv = (void *)&ecb; ecb.out_line = out_line; ecb.out_hunk = NULL;
  g_ret = nondet_int();
  int r = xdl_emit_diffrec(rec, size, pre, psize, &ecb);
  int incomplete = size > 0 && rec[size - 1] != '\n';
  __CPROVER_assert(g_calls == 1 && g_priv == ecb.priv, "one call with priv");
  __CPROVER_assert(g_n == (incomplete ? 3 : 2), "marker only for an incomplete line");
  __CPROVER_assert(g_ptr[0] == pre && g_size[0] == psize && g_ptr[1] == rec && g_size[1] == size, "pre, then the line");
  if (incomplete) {
    static const char marker[] = "\n\\ No newline at end of file\n";
    __CPROVER_assert(g_size[2] == sizeof marker - 1, "marker length");
    int j = nondet_int(); __CPROVER_assume(0 <= j && j < (int)sizeof marker - 1);
    __CPROVER_assert(__CPROVER_r_ok(g_ptr[2], g_size[2]) && g_ptr[2][j] == marker[j], "marker text");
  }
  __CPROVER_assert(r == (g_ret < 0 ? -1 : 0), "result");
}

// xdl_mmfile_first / xdl_mmfile_size: the single buffer of an mmfile and its size.
void h_mmfile(void) {
  mmfile_t m; m.ptr = (char *)nondet_long(); m.size = nondet_int();
  long size = nondet_long();
  void *p = xdl_mmfile_first(&m, &size);
  __CPROVER_assert(p == m.ptr && size == m.size, "first");
  __CPROVER_assert(xdl_mmfile_size(&m) == m.size, "size");
}

// xdl_cha_init is proved with WP (../wp/): its spec multiplies 64-bit numbers, which CBMC's
// SAT encoding does not finish on.

// xdl_cha_alloc on any store that xdl_cha_init and earlier xdl_cha_alloc calls can make:
// blocks of sizeof(chanode_t) + nsize bytes in a list head..tail, the current block is the
// tail, and its first icurr bytes after the header are the items handed out so far. Returns
// isize fresh writable bytes that overlap no earlier item: the next free slot of the tail, or
// the first slot of a new block appended to the list; NULL (store unchanged) only when a new
// block was needed and malloc failed.
// The store invariant is "nsize = k * isize and icurr = j * isize with 0 <= j <= k". This
// harness uses what follows from it without multiplying (SLOTS below); ../wp/ proves that
// the invariant gives SLOTS and that each call keeps the invariant (lemma cha_slots).
#define SLOTS(icurr, nsize, isize) (0 <= (icurr) && (icurr) <= (nsize) && ((icurr) == (nsize) || (icurr) + (isize) <= (nsize)))
void h_cha_alloc(void) {
  chastore_t c; long isize = nondet_long();
  c.nsize = nondet_long();
  __CPROVER_assume(isize >= 1 && c.nsize >= isize && (size_t)c.nsize + sizeof(chanode_t) <= MAX_OBJ);
  c.isize = isize; c.sncur = (chanode_t *)nondet_long(); c.scurr = nondet_long();
  chanode_t *other = __CPROVER_allocate(sizeof(chanode_t) + c.nsize, 0);
  if (nondet_bool()) { c.head = c.tail = c.ancur = NULL; }
  else {
    chanode_t *t = __CPROVER_allocate(sizeof(chanode_t) + c.nsize, 0);
    t->icurr = nondet_long(); t->next = NULL;
    __CPROVER_assume(SLOTS(t->icurr, c.nsize, isize));
    c.tail = c.ancur = t;
    c.head = nondet_bool() ? t : other;   // one block, or more (only head and tail matter)
  }
  chastore_t old = c; long old_icurr = old.tail ? old.tail->icurr : 0;
  char *r = xdl_cha_alloc(&c);
  int need_block = old.tail == NULL || old_icurr == c.nsize;
  __CPROVER_assert(c.isize == old.isize && c.nsize == old.nsize && c.sncur == old.sncur && c.scurr == old.scurr, "sizes kept");
  if (r == NULL) {
    __CPROVER_assert(need_block, "fails only when it needs a block");
    __CPROVER_assert(c.head == old.head && c.tail == old.tail && c.ancur == old.ancur
                     && (!old.tail || (old.tail->icurr == old_icurr && old.tail->next == NULL)), "store unchanged");
    return;
  }
  __CPROVER_assert(__CPROVER_w_ok(r, isize), "isize writable bytes");
  __CPROVER_assert(c.ancur == c.tail && c.tail->next == NULL, "the tail is the current block");
  if (!need_block) {
    __CPROVER_assert(c.tail == old.tail && c.head == old.head, "same block");
    __CPROVER_assert(r == (char *)old.tail + sizeof(chanode_t) + old_icurr && c.tail->icurr == old_icurr + isize,
                     "next free slot, after every earlier item");
  } else {
    __CPROVER_assert(c.tail != old.tail && c.tail != other && __CPROVER_POINTER_OFFSET(c.tail) == 0
                     && __CPROVER_OBJECT_SIZE(c.tail) == sizeof(chanode_t) + c.nsize, "new block");
    __CPROVER_assert(r == (char *)c.tail + sizeof(chanode_t) && c.tail->icurr == isize, "its first slot");
    if (old.tail) __CPROVER_assert(old.tail->next == c.tail && c.head == old.head && old.tail->icurr == old_icurr, "appended");
    else __CPROVER_assert(c.head == c.tail, "first block");
  }
}

// ---- hunk headers
static long h_a, h_b, h_c, h_d, h_fl; static const char *h_f; static int h_calls, h_ret;
static int out_hunk(void *priv, long a, long b, long c, long d, const char *f, long fl) {
  h_calls++; h_a = a; h_b = b; h_c = c; h_d = d; h_f = f; h_fl = fl; return h_ret;
}
// xdl_emit_hunk_hdr with an out_hunk callback: passes the hunk as (start before the hunk
// when it is empty, count) for each side, as unified diff does, and the function name.
void h_emit_hunk_hdr_cb(void) {
  long s1 = nondet_long(), c1 = nondet_long(), s2 = nondet_long(), c2 = nondet_long(), fl = nondet_long();
  // xemit.c calls it with s = (0-based start) + 1 and c = count >= 0
  __CPROVER_assume(s1 >= 1 && c1 >= 0 && s2 >= 1 && c2 >= 0);
  const char *f = (const char *)nondet_long();
  xdemitcb_t ecb; ecb.priv = &ecb; ecb.out_line = out_line; ecb.out_hunk = out_hunk;
  h_ret = nondet_int();
  int r = xdl_emit_hunk_hdr(s1, c1, s2, c2, f, fl, &ecb);
  __CPROVER_assert(h_calls == 1 && g_calls == 0, "out_hunk only");
  __CPROVER_assert(h_a == (c1 ? s1 : s1 - 1) && h_b == c1 && h_c == (c2 ? s2 : s2 - 1) && h_d == c2, "range");
  __CPROVER_assert(h_f == f && h_fl == fl, "function name");
  __CPROVER_assert(r == (h_ret < 0 ? -1 : 0), "result");
}

// xdl_emit_hunk_hdr without out_hunk: one out_line call with the unified-diff hunk header
// "@@ -A[,c1] +B[,c2] @@[ func]\n" where A = s1 (s1 - 1 for an empty side), ",c" is left
// out when c is 1, and the function name is cut so the whole line is at most 128 bytes.
// For the upstream code (negative numbers wrong) the harness keeps to the range xemit.c
// uses (s >= 1, c >= 0); the fixed code is proved for every long except the two cases
// where s - 1 itself overflows. func has funclen readable bytes.
static char exp_buf[160]; static int exp_len, exp_hdr; static const char *exp_func;
static int out_line_hdr(void *priv, mmbuffer_t *mb, int n) {
  g_calls++;
  __CPROVER_assert(n == 1 && mb->size == exp_len, "one buffer of the expected length");
  int j = nondet_int(); __CPROVER_assume(0 <= j && j < exp_len);
  char want = j < exp_hdr ? exp_buf[j] : j == exp_len - 1 ? '\n' : j == exp_hdr ? ' ' : exp_func[j - exp_hdr - 1];
  __CPROVER_assert(__CPROVER_r_ok(mb->ptr, mb->size) && mb->ptr[j] == want, "header text");
  return g_ret;
}
void h_emit_hunk_hdr_text(void) {
  long s1 = nondet_long(), c1 = nondet_long(), s2 = nondet_long(), c2 = nondet_long(), fl = nondet_long();
#ifdef FULL_RANGE
  __CPROVER_assume(!(c1 == 0 && s1 == LONG_MIN) && !(c2 == 0 && s2 == LONG_MIN));
#else
  __CPROVER_assume(s1 >= 1 && c1 >= 0 && s2 >= 1 && c2 >= 0);
#endif
  size_t fsize = nondet_size(); __CPROVER_assume(fsize <= MAX_OBJ);
  char *f = nondet_bool() ? NULL : __CPROVER_allocate(fsize, 0);
  __CPROVER_assume(fl >= 0 && (f == NULL || (size_t)fl <= fsize));
  int k = 0;
  exp_buf[k++] = '@'; exp_buf[k++] = '@'; exp_buf[k++] = ' '; exp_buf[k++] = '-';
  k += ref_dec(exp_buf + k, c1 ? s1 : s1 - 1);
  if (c1 != 1) { exp_buf[k++] = ','; k += ref_dec(exp_buf + k, c1); }
  exp_buf[k++] = ' '; exp_buf[k++] = '+';
  k += ref_dec(exp_buf + k, c2 ? s2 : s2 - 1);
  if (c2 != 1) { exp_buf[k++] = ','; k += ref_dec(exp_buf + k, c2); }
  exp_buf[k++] = ' '; exp_buf[k++] = '@'; exp_buf[k++] = '@';
  exp_hdr = k; exp_func = f;
  long m = 0;
  if (f && fl) { m = fl < 128 - k - 2 ? fl : 128 - k - 2; exp_len = k + 1 + (int)m + 1; }
  else exp_len = k + 1;
  __CPROVER_assert(exp_len <= 128, "fits");
  xdemitcb_t ecb; ecb.priv = &ecb; ecb.out_line = out_line_hdr; ecb.out_hunk = NULL;
  g_ret = nondet_int();
  int r = xdl_emit_hunk_hdr(s1, c1, s2, c2, f, fl, &ecb);
  __CPROVER_assert(g_calls == 1, "one line");
  __CPROVER_assert(r == (g_ret < 0 ? -1 : 0), "result");
}

// ---- xdl_fall_back_diff: diff the line ranges [line1, line1 + count1) and
// [line2, line2 + count2) (1-based) of an environment again on their own, as a fresh
// pair of files made of the bytes from the first record of each range to the end of its
// last, with the same parameters; on success copy the line changes found into the
// ranges of rchg and free the temporary environment, return 0; on failure return -1
// and change nothing. xdl_do_diff is modelled by its contract (CLAIM.md): it fails, or
// fills env with an rchg of at least one byte per record of each file.
static int dd_calls, dd_ret, fe_calls; static mmfile_t dd_m1, dd_m2; static xpparam_t const *dd_xpp;
static xdfenv_t *dd_env, *fe_env; static long dd_n1, dd_n2;
int xdl_do_diff(mmfile_t *mf1, mmfile_t *mf2, xpparam_t const *xpp, xdfenv_t *xe) {
  dd_calls++; dd_m1 = *mf1; dd_m2 = *mf2; dd_xpp = xpp; dd_env = xe;
  if (dd_ret < 0) return dd_ret;
  size_t a = nondet_size(), b = nondet_size();
  __CPROVER_assume(a >= dd_n1 && b >= dd_n2 && a <= MAX_OBJ && b <= MAX_OBJ);
  xe->xdf1.rchg = __CPROVER_allocate(a, 0); xe->xdf2.rchg = __CPROVER_allocate(b, 0);
  return 0;
}
static char *fe_r1, *fe_r2;
void xdl_free_env(xdfenv_t *xe) { fe_calls++; fe_env = xe; fe_r1 = xe->xdf1.rchg; fe_r2 = xe->xdf2.rchg; }

static char *range_file(xdfile_t *x, int line, int count, char **start, long *size) {
  long nrec = nondet_long();
  __CPROVER_assume(line >= 1 && count >= 1 && line - 1 + (long)count <= nrec && nrec < INT_MAX);   // records of an mmfile (int size): CLAIM.md
  x->nrec = nrec;
  x->recs = __CPROVER_allocate(nrec * sizeof(xrecord_t *), 0);
  // the records lie in order in one mmfile buffer (int size)
  long bsize = nondet_long(), a = nondet_long(), b = nondet_long(), lsz = nondet_long();
  __CPROVER_assume(0 <= bsize && bsize <= INT_MAX && 0 <= a && a <= bsize && 0 <= b && b <= bsize && 0 <= lsz && lsz <= bsize && (count == 1 ? b == a : a <= b) && b + lsz <= bsize);
  char *buf = __CPROVER_allocate(bsize, 0);
  xrecord_t *r1 = __CPROVER_allocate(sizeof(xrecord_t), 0), *r2 = count == 1 ? r1 : __CPROVER_allocate(sizeof(xrecord_t), 0);
  r1->ptr = buf + a; r2->ptr = buf + b; r2->size = lsz;
  if (count > 1) { r1->size = nondet_long(); __CPROVER_assume(0 <= r1->size && r1->size <= bsize && a + r1->size <= b); }
  x->recs[line - 1] = r1; x->recs[line + count - 2] = r2;
  size_t rs = nondet_size(); __CPROVER_assume(rs >= line - 1 + (size_t)count && rs <= MAX_OBJ);
  x->rchg = __CPROVER_allocate(rs, 0);
  *start = buf + a; *size = b + lsz - a;
  return x->rchg;
}
void h_fall_back_diff(void) {
  xdfenv_t e; xpparam_t xpp;
  int line1 = nondet_int(), count1 = nondet_int(), line2 = nondet_int(), count2 = nondet_int();
  char *p1, *p2; long z1, z2;
  char *rc1 = range_file(&e.xdf1, line1, count1, &p1, &z1), *rc2 = range_file(&e.xdf2, line2, count2, &p2, &z2);
  dd_n1 = count1; dd_n2 = count2; dd_ret = nondet_int();
  long j = nondet_long(), i = nondet_long();
  __CPROVER_assume(0 <= j && (size_t)j < __CPROVER_OBJECT_SIZE(rc1) && 0 <= i && (size_t)i < __CPROVER_OBJECT_SIZE(rc2));
  char o1 = rc1[j], o2 = rc2[i];
  int r = xdl_fall_back_diff(&e, &xpp, line1, count1, line2, count2);
  __CPROVER_assert(dd_calls == 1 && dd_xpp == &xpp && dd_env != &e, "one diff into a fresh environment");
  __CPROVER_assert(dd_m1.ptr == p1 && dd_m1.size == z1 && dd_m2.ptr == p2 && dd_m2.size == z2, "the two ranges as files");
  __CPROVER_assert(e.xdf1.rchg == rc1 && e.xdf2.rchg == rc2, "rchg arrays kept");
  if (dd_ret < 0) {
    __CPROVER_assert(r == -1 && fe_calls == 0 && rc1[j] == o1 && rc2[i] == o2, "failure changes nothing");
    return;
  }
  __CPROVER_assert(r == 0 && fe_calls == 1 && fe_env == dd_env, "success frees the temporary environment");
  if (j >= line1 - 1 && j < (long)line1 - 1 + count1) __CPROVER_assert(rc1[j] == fe_r1[j - (line1 - 1)], "file 1 range copied");
  else __CPROVER_assert(rc1[j] == o1, "file 1 outside the range kept");
  if (i >= line2 - 1 && i < (long)line2 - 1 + count2) __CPROVER_assert(rc2[i] == fe_r2[i - (line2 - 1)], "file 2 range copied");
  else __CPROVER_assert(rc2[i] == o2, "file 2 outside the range kept");
}
