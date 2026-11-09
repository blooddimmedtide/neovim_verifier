#include <stdlib.h>
#include <string.h>
#include "fn_sort.c"
#include "spec_sort.h"
#ifndef N
#define N 6
#endif
long nondet_long(void); char nondet_char(void);
static char *mk(void) {
  long len = nondet_long(); __CPROVER_assume(len >= 0 && len <= N);
  char *s = malloc(len + 1); __CPROVER_assume(s != NULL);
  for (long i = 0; i < len; i++) { s[i] = nondet_char(); __CPROVER_assume(s[i] != 0); }
  s[len] = 0; return s;
}
static int sgn(int v) { return (v > 0) - (v < 0); }
int main(void) {
  char *a = mk(), *b = mk();
  int r = sort_func_compare(&a, &b);
  __CPROVER_assert(sgn(r) == ref_sort(a, b), "comparator sign matches reference");
  return 0;
}
