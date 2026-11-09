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
