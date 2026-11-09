// CBMC: foldFind meets spec.h for every valid fold array of up to N folds and every lnum.
#include <stdlib.h>
#include "spec.h"
#include FOLD_FIND_C
#ifndef N
#define N 6
#endif
int nondet_int(void);
void h_foldFind(void) {
  const int n = N;                         // one run per array length 0..N (run_cbmc.sh)
  fold_T *f = n ? malloc(sizeof(fold_T) * n) : NULL;  // exact size: reading past the end fails
  for (int k = 0; k < n; k++) { f[k].fd_top = nondet_int(); f[k].fd_len = nondet_int(); }
  if (!spec_valid(f, n)) return;           // documented fold-array invariant (CLAIM.md)
  garray_T ga = { .ga_len = n, .ga_data = f };
  linenr_T lnum = nondet_int();
  fold_T *res = (fold_T *)1;
  bool r = foldFind(&ga, lnum, &res);
  int c = spec_containing(f, n, lnum);
  if (n == 0) { __CPROVER_assert(!r && res == NULL, "empty: false, NULL"); return; }
  __CPROVER_assert(r == (c >= 0), "returns true iff a fold contains lnum");
  if (c >= 0) __CPROVER_assert(res == f + c, "points at the containing fold");
  else __CPROVER_assert(res == f + spec_below(f, n, lnum), "points at the first fold below lnum");
}

// foldReverseOrder (undocumented; meaning from its name and its callers in foldMoveRange,
// fold.c:2734-2738, which rotate a block of folds by three reversals): reverse entries
// start..end inclusive and leave every other entry alone. When start >= end nothing changes.
// Precondition (all callers): 0 <= start and end < ga_len whenever start < end.
static bool same(const fold_T *a, const fold_T *b) {
  return a->fd_top == b->fd_top && a->fd_len == b->fd_len && a->fd_flags == b->fd_flags
      && a->fd_small == b->fd_small && a->fd_nested.ga_len == b->fd_nested.ga_len
      && a->fd_nested.ga_maxlen == b->fd_nested.ga_maxlen
      && a->fd_nested.ga_itemsize == b->fd_nested.ga_itemsize
      && a->fd_nested.ga_growsize == b->fd_nested.ga_growsize
      && a->fd_nested.ga_data == b->fd_nested.ga_data;
}
char nondet_char(void);
void *nondet_ptr(void);
void h_foldReverseOrder(void) {
  const int n = N;
  fold_T *f = n ? malloc(sizeof(fold_T) * n) : NULL;
  fold_T old[N + 1];
  for (int k = 0; k < n; k++) {
    f[k].fd_top = nondet_int(); f[k].fd_len = nondet_int(); f[k].fd_flags = nondet_char();
    f[k].fd_small = (TriState)nondet_int();
    f[k].fd_nested.ga_len = nondet_int(); f[k].fd_nested.ga_maxlen = nondet_int();
    f[k].fd_nested.ga_itemsize = nondet_int(); f[k].fd_nested.ga_growsize = nondet_int();
    f[k].fd_nested.ga_data = nondet_ptr();
    old[k] = f[k];
  }
  garray_T ga = { .ga_len = n, .ga_data = f };
  linenr_T s = nondet_int(), e = nondet_int();
  if (s < e && !(0 <= s && e < n)) return;  // caller precondition (CLAIM.md)
  foldReverseOrder(&ga, s, e);
  for (int k = 0; k < n; k++) {
    if (s < e && s <= k && k <= e) __CPROVER_assert(same(&f[k], &old[s + e - k]), "reversed");
    else __CPROVER_assert(same(&f[k], &old[k]), "untouched");
  }
}
