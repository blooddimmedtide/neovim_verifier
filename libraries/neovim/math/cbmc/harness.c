// CBMC proofs of full functional correctness of src/nvim/math.c, every input.
#include <math.h>
#include <limits.h>
#include <stdint.h>
#include MATH_C

uint64_t nondet_u64(void);
int64_t nondet_i64(void);
int nondet_int(void);
double nondet_double(void);

// IEEE 754 double classes (CBMC's own float semantics, not math.c's bit test).
void h_classify(void) {
  double d = nondet_double();
  int want = __CPROVER_isnand(d) ? FP_NAN : __CPROVER_isinfd(d) ? FP_INFINITE
           : d == 0.0 ? FP_ZERO : __CPROVER_isnormald(d) ? FP_NORMAL : FP_SUBNORMAL;
  __CPROVER_assert(xfpclassify(d) == want, "xfpclassify");
  __CPROVER_assert(xisinf(d) == (want == FP_INFINITE), "xisinf");
  __CPROVER_assert(xisnan(d) == (want == FP_NAN), "xisnan");
}

// xctz: 64 for 0, else the index of the lowest set bit.
void h_ctz(void) {
  uint64_t x = nondet_u64();
  int r = xctz(x);
  if (x == 0) { __CPROVER_assert(r == 64, "ctz(0) = 64"); return; }
  __CPROVER_assert(r >= 0 && r < 64, "range");
  __CPROVER_assert(((x >> r) & 1) == 1, "bit r set");
  __CPROVER_assert((x & ((((uint64_t)1) << r) - 1)) == 0, "bits below r clear");
}

// xpopcount: the number of set bits.
void h_popcount(void) {
  uint64_t x = nondet_u64();
  unsigned n = 0;
  for (int i = 0; i < 64; i++) n += (unsigned)((x >> i) & 1);
  __CPROVER_assert(xpopcount(x) == n, "popcount");
}

// vim_append_digit_int: for value >= 0 and a digit 0..9 (its only caller,
// normal.c, keeps the count non-negative), appends the digit exactly when the
// result fits in an int; otherwise FAIL and the value is unchanged.
void h_append_digit(void) {
  int v = nondet_int(), d = nondet_int();
  __CPROVER_assume(v >= 0 && d >= 0 && d <= 9);
  int old = v;
  int r = vim_append_digit_int(&v, d);
  int64_t want = (int64_t)old * 10 + d;
  if (want <= INT_MAX) __CPROVER_assert(r == OK && v == want, "appended");
  else __CPROVER_assert(r == FAIL && v == old, "overflow refused");
}

// trim_to_int: clamps to [INT_MIN, INT_MAX].
void h_trim(void) {
  int64_t x = nondet_i64();
  int64_t want = x > INT_MAX ? INT_MAX : x < INT_MIN ? INT_MIN : x;
  __CPROVER_assert(trim_to_int(x) == want, "clamp");
}
