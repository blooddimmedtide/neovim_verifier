// CBMC proofs of src/nvim/indent.c tabstop helpers against an independent reference.
// Model of a tab-stop list (:help 'vartabstop'): stops at S_1 = w_1, S_2 = S_1 + w_2, ...,
// S_n, then every w_n after S_n. No list (NULL or vts[0] == 0): stops every ts.
// The vts array has exactly vts[0] + 1 ints, so any read past its end fails.
#include <stdlib.h>
#include INDENT_C

#ifndef MAXN
#define MAXN 4
#endif
int nondet_int(void);
long long nondet_ll(void);
_Bool nondet_bool(void);

static int n_, w_[MAXN + 2];   // reference copy of the list (1-based)
// k-th stop (k >= 0; stop 0 is column 0).
static long long stop(long long k) {
  long long s = 0;
  for (int i = 1; i <= n_; i++) { if (i > k) return s; s += w_[i]; }
  return s + (k - n_) * w_[n_];
}
// Number of stops at columns 1..x (x >= 0).
static long long count(long long x) {
  long long s = 0;
  for (int i = 1; i <= n_; i++) { s += w_[i]; if (s > x) return i - 1; }
  return n_ + (x - s) / w_[n_];
}

// Build a list with n in 0..MAXN entries, each in 1..TABSTOP_MAX (what tabstop_set makes),
// or NULL. ts is the uniform width the reference uses when there is no list.
static colnr_T *mk(long long ts) {
  if (nondet_bool()) { n_ = 1; w_[1] = (int)ts; return NULL; }
  int n = nondet_int(); __CPROVER_assume(n >= 0 && n <= MAXN);
  colnr_T *v = malloc((size_t)(n + 1) * sizeof(int)); __CPROVER_assume(v != NULL); v[0] = n;
  for (int i = 1; i <= n; i++) {
    int w = nondet_int(); __CPROVER_assume(w >= 1 && w <= TABSTOP_MAX); v[i] = w; w_[i] = w;
  }
  if (n == 0) { n_ = 1; w_[1] = (int)ts; } else n_ = n;
  return v;
}

void h_padding(void) {
  OptInt ts_arg = nondet_ll(); __CPROVER_assume(ts_arg >= 0 && ts_arg <= TABSTOP_MAX);
  colnr_T col = nondet_int(); __CPROVER_assume(col >= 0);
  colnr_T *v = mk(ts_arg == 0 ? 8 : ts_arg);
  __CPROVER_assert(tabstop_padding(col, ts_arg, v) == stop(count(col) + 1) - col,
                   "padding = next stop after col - col");
}

void h_at(void) {
  OptInt ts = nondet_ll(); __CPROVER_assume(ts >= 1 && ts <= TABSTOP_MAX);
  colnr_T col = nondet_int(); __CPROVER_assume(col >= 0);
  bool left = nondet_bool();
  colnr_T *v = mk(ts);
  long long c = count(col), want;
  int r = tabstop_at(col, ts, v, left);
  if (left && c == 0) {
    // Left of the first stop the comment only promises "at least that distance" (col).
    __CPROVER_assert(r >= col, "tabstop_at left of first stop >= col");
    return;
  }
  if (!left) want = stop(c + 1) - stop(c);  // interval holding col
  else want = stop(c) - stop(c - 1);        // interval to its left
  __CPROVER_assert(r == want, "tabstop_at");
}

void h_start(void) {
  int ts = nondet_int(); __CPROVER_assume(ts >= 1 && ts <= TABSTOP_MAX);
  colnr_T col = nondet_int(); __CPROVER_assume(col >= 0);
  colnr_T *v = mk(ts);
  __CPROVER_assert(tabstop_start(col, ts, v) == stop(count(col)), "last stop <= col");
}

void h_fromto(void) {
  int ts_arg = nondet_int(); __CPROVER_assume(ts_arg >= 0 && ts_arg <= TABSTOP_MAX);
  buf_T b; b.b_p_ts = nondet_ll(); __CPROVER_assume(b.b_p_ts >= 1 && b.b_p_ts <= TABSTOP_MAX);
  curbuf = &b;
  colnr_T s = nondet_int(), e = nondet_int(); __CPROVER_assume(s >= 0 && s <= e);
  colnr_T *v = mk(ts_arg == 0 ? b.b_p_ts : ts_arg);
  int nt, ns;
  tabstop_fromto(s, e, ts_arg, v, &nt, &ns);
  long long tabs = count(e) - count(s);
  __CPROVER_assert(nt == tabs, "ntabs = stops in (start, end]");
  __CPROVER_assert(ns == e - (tabs > 0 ? stop(count(e)) : s), "nspcs = end - last tab end");
}

void h_count_first(void) {
  if (nondet_bool()) {
    __CPROVER_assert(tabstop_count(NULL) == 0, "count(NULL)");
    __CPROVER_assert(tabstop_first(NULL) == 8, "first(NULL)");
    return;
  }
  int n = nondet_int(); __CPROVER_assume(n >= 1 && n <= MAXN);
  colnr_T *v = malloc((size_t)(n + 1) * sizeof(int)); __CPROVER_assume(v != NULL); v[0] = n;
  for (int i = 1; i <= n; i++) { v[i] = nondet_int(); __CPROVER_assume(v[i] >= 1 && v[i] <= TABSTOP_MAX); }
  __CPROVER_assert(tabstop_count(v) == n, "count");
  __CPROVER_assert(tabstop_first(v) == v[1], "first");
}
