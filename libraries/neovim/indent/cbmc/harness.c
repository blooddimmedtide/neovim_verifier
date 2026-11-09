// CBMC harnesses: full functional correctness of the tabstop helpers of indent.c
// against spec.h, for every col in [0, INT_MAX], every width in [1, TABSTOP_MAX]
// and 'vartabstop' lists of up to MAXN entries (bounded proof; see CLAIM.md).
#include INDENT_C
#include <limits.h>
#include "spec.h"
#ifndef MAXN
#define MAXN 3
#endif
#define TABSTOP_MAX 9999  // option_vars.h
int nondet_int(void); int64_t nondet_i64(void); _Bool nondet_bool(void);
buf_T *curbuf;
void *xmalloc(size_t size) { void *p = malloc(size); if (p == NULL) abort(); return p; }

// Builds either NULL, {0} (count 0, means "use ts"), or an exact-size list as tabstop_set makes.
static int *mk_vts(int *n_out, int ts, int lw[MAXN + 1])
{
  int n = nondet_int();
  __CPROVER_assume(n >= -1 && n <= MAXN);
  int *vts = NULL;
  if (n >= 0) {
    vts = malloc((size_t)(n + 1) * sizeof(int));
    vts[0] = n;
    for (int k = 1; k <= n; k++) {
      vts[k] = nondet_int();
      __CPROVER_assume(vts[k] >= 1 && vts[k] <= TABSTOP_MAX);
    }
  }
  if (n <= 0) { lw[1] = ts; *n_out = 1; } else { for (int k = 1; k <= n; k++) lw[k] = vts[k]; *n_out = n; }
  return vts;
}
static int nd_col(void) { int c = nondet_int(); __CPROVER_assume(c >= 0); return c; }
static int nd_ts(void) { int t = nondet_int(); __CPROVER_assume(t >= 1 && t <= TABSTOP_MAX); return t; }

void h_padding(void)
{
  int col = nd_col(); OptInt ts_arg = nondet_i64();
  __CPROVER_assume(ts_arg >= 0 && ts_arg <= TABSTOP_MAX);   // 'tabstop' range; 0 means 8 (documented)
  int lw[MAXN + 1], n; int *vts = mk_vts(&n, ts_arg == 0 ? 8 : (int)ts_arg, lw);
  int r = tabstop_padding(col, ts_arg, vts);
  RefPos p = ref_pos(col, lw, n);
  assert(r == p.next - col);
}

void h_at(void)
{
  int col = nd_col(); int ts = nd_ts(); bool left = nondet_bool();
  int lw[MAXN + 1], n; int *vts = mk_vts(&n, ts, lw);
  int r = tabstop_at(col, ts, vts, left);
  RefPos p = ref_pos(col, lw, n);
  if (!left) {
    assert(r == p.next - p.prev);                 // width of the tab interval under col
  } else if (p.prev == 0) {
    assert(r >= col);                             // first interval: at least the distance to the margin (0 at col 0)
  } else {
    RefPos q = ref_pos(p.prev - 1, lw, n);
    assert(r == q.next - q.prev);                 // width of the interval to the left
  }
}

void h_start(void)
{
  int col = nd_col(); int ts = nd_ts();
  int lw[MAXN + 1], n; int *vts = mk_vts(&n, ts, lw);
  int r = tabstop_start(col, ts, vts);
  assert(r == ref_pos(col, lw, n).prev);
}

void h_fromto(void)
{
  int s = nd_col(), e = nd_col(); __CPROVER_assume(s <= e);   // callers pass start <= end
  int ts_arg = nondet_int(); __CPROVER_assume(ts_arg >= 0 && ts_arg <= TABSTOP_MAX);
  buf_T b; b.b_p_ts = nd_ts(); curbuf = &b;                     // ts_arg == 0 means curbuf's 'tabstop'
  int ts = ts_arg == 0 ? (int)b.b_p_ts : ts_arg;
  int lw[MAXN + 1], n; int *vts = mk_vts(&n, ts, lw);
  int ntabs, nspcs;
  tabstop_fromto(s, e, ts_arg, vts, &ntabs, &nspcs);
  RefPos ps = ref_pos(s, lw, n), pe = ref_pos(e, lw, n);
  if (ps.next > e) { assert(ntabs == 0 && nspcs == e - s); }
  else { assert(ntabs == pe.idx - ps.idx && nspcs == e - pe.prev); }
}

void h_copy_count_first(void)
{
  int ts = nd_ts(); int lw[MAXN + 1], n; int *vts = mk_vts(&n, ts, lw);
  int *c = tabstop_copy(vts);
  if (vts == NULL) { assert(c == NULL); assert(tabstop_count(vts) == 0); assert(tabstop_first(vts) == 8); return; }
  assert(c != NULL && c != vts);
  for (int k = 0; k <= vts[0]; k++) assert(c[k] == vts[k]);
  assert(__CPROVER_OBJECT_SIZE(c) == (vts[0] + 1) * sizeof(int));
  assert(tabstop_count(vts) == vts[0]);
  if (vts[0] >= 1) assert(tabstop_first(vts) == vts[1]);  // lists from tabstop_set have >= 1 entry
}
