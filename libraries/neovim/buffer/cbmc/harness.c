// CBMC harnesses for two self-contained helpers of src/nvim/buffer.c.
// Specs come from the doc comments and the callers' contract, not from the code.
#include <stdint.h>
#include <time.h>
#include <assert.h>
int64_t nondet_i64(void);
time_t nondet_time(void);
// Minimal buf_T: only the field the comparator reads. Layout of the rest is irrelevant.
typedef struct { int b_fnum; time_t b_last_used; } buf_T;
#include "out/calc_percentage.c"
#include "out/buf_time_compare.c"

// calc_percentage: "the percentage that part is of whole".
// Contract taken from every caller in buffer.c: 0 <= part <= whole, whole >= 1
// (fileinfo: 1 <= cursor lnum <= line_count; get_rel_pos: above, below >= 1).
// Spec: result r is floor(100*part/whole), or one above it (the documented
// divide-first path for large part). Also 0 <= r <= 100. Exact for part <= 1e6.
void h_calc_percentage(void) {
  int64_t part = nondet_i64(), whole = nondet_i64();
  __CPROVER_assume(whole >= 1 && part >= 0 && part <= whole);
  int r = calc_percentage(part, whole);
  // Reference in 128-bit arithmetic (no overflow possible).
  __int128 f = ((__int128)part * 100) / whole;
  assert(r >= 0 && r <= 100);
  assert(r == f || r == f + 1);
  if (part <= 1000000) assert(r == f);
}

// Outside the caller contract: whole in [1,99] with part > 1e6 divides by zero.
// Kept as a documented check (expected to FAIL) in harness_outside.c.

// buf_time_compare: qsort comparator, most recently used first.
// Spec: sign is -1 when buf1 newer, +1 when older, 0 when equal; antisymmetric.
void h_buf_time_compare(void) {
  buf_T a, b;
  a.b_last_used = nondet_time(); b.b_last_used = nondet_time();
  buf_T *pa = &a, *pb = &b;
  int r = buf_time_compare(&pa, &pb);
  int s = buf_time_compare(&pb, &pa);
  if (a.b_last_used > b.b_last_used) assert(r == -1);
  if (a.b_last_used < b.b_last_used) assert(r == 1);
  if (a.b_last_used == b.b_last_used) assert(r == 0);
  assert(r == -s);
  // Self-comparison is 0 (qsort may compare an element with itself).
  assert(buf_time_compare(&pa, &pa) == 0);
}

// Called from ExpandBufnames on a bufmatch_T array: its first member is buf_T *buf,
// so reading the element as buf_T ** is the first member (C11 6.7.2.1p15).
typedef struct { buf_T *buf; char *match; } bufmatch_T;
void h_buf_time_compare_bufmatch(void) {
  buf_T a, b;
  a.b_last_used = nondet_time(); b.b_last_used = nondet_time();
  bufmatch_T m[2] = { { &a, 0 }, { &b, 0 } };
  int r = buf_time_compare(&m[0], &m[1]);
  assert(r == (a.b_last_used == b.b_last_used ? 0 : a.b_last_used > b.b_last_used ? -1 : 1));
}
