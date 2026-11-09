// Differential test: compiled foldFind (gcc -O2) against spec.h. Exhaustive over all valid
// arrays of up to 4 folds with tops/lens in a small window, every lnum in the window,
// plus the large-value edges near INT32_MAX.
#include <stdio.h>
#include <stdlib.h>
#include "spec.h"
#include FOLD_FIND_C
static long checked, bad;
static fold_T f[4];
static void check(int n) {
  garray_T ga = { .ga_len = n, .ga_data = n ? f : NULL };
  for (linenr_T l = -2; l <= 14; l++) {
    fold_T *res; bool r = foldFind(&ga, l, &res); int c = spec_containing(f, n, l);
    bool ok = n == 0 ? (!r && res == NULL)
            : (r == (c >= 0) && res == (c >= 0 ? f + c : f + spec_below(f, n, l)));
    checked++; if (!ok) { bad++; if (bad < 5) printf("mismatch n=%d lnum=%d\n", n, l); }
  }
}
static void rec(int k, int n) {
  if (k == n) { if (spec_valid(f, n)) check(n); return; }
  for (int t = 0; t <= 12; t++) for (int len = 1; len <= 4; len++) { f[k].fd_top = t; f[k].fd_len = len; rec(k + 1, n); }
}
int main(void) {
  for (int n = 0; n <= 4; n++) rec(0, n);
  // edge: one fold ending exactly at INT32_MAX
  f[0].fd_top = INT32_MAX - 3; f[0].fd_len = 3;
  garray_T ga = { .ga_len = 1, .ga_data = f }; fold_T *res;
  if (!foldFind(&ga, INT32_MAX - 1, &res) || res != f) bad++;
  if (foldFind(&ga, INT32_MAX, &res) || res != f + 1) bad++;
  printf("checked %ld cases, %ld mismatches\n", checked + 2, bad);
  return bad != 0;
}
