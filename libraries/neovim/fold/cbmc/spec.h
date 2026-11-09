// Reference meaning of foldFind, written from its doc comment (fold.c:1015-1019), not its code.
// A fold array is valid when folds have fd_len >= 1, are sorted by fd_top and do not overlap
// (fold.c:62-65 and every insertion site keep this), and top+len fits in linenr_T.
#pragma once
#include "fold_types.h"
static bool spec_valid(const fold_T *f, int n) {
  for (int k = 0; k < n; k++) {
    if (f[k].fd_len < 1 || f[k].fd_top < 0) return false;
    if ((int64_t)f[k].fd_top + f[k].fd_len > INT32_MAX) return false;
    if (k > 0 && (int64_t)f[k - 1].fd_top + f[k - 1].fd_len > f[k].fd_top) return false;
  }
  return true;
}
// Index of the fold containing lnum, or -1.
static int spec_containing(const fold_T *f, int n, linenr_T lnum) {
  for (int k = 0; k < n; k++)
    if (f[k].fd_top <= lnum && (int64_t)lnum < (int64_t)f[k].fd_top + f[k].fd_len) return k;
  return -1;
}
// "the first fold below it": number of folds that start at or above lnum.
static int spec_below(const fold_T *f, int n, linenr_T lnum) {
  int c = 0;
  for (int k = 0; k < n; k++) if (f[k].fd_top <= lnum) c++;
  return c;
}
