// Documents behaviour outside the caller contract (expected to FAIL: division by zero).
#include <stdint.h>
int64_t nondet_i64(void);
#include "out/calc_percentage.c"
void h_outside(void) {
  int64_t part = nondet_i64(), whole = nondet_i64();
  __CPROVER_assume(whole >= 1 && part >= 0);
  (void)calc_percentage(part, whole);
}
