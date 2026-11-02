// CBMC proofs for utf_cp_bounds_len / utf_cp_bounds (src/nvim/mbyte.c).
#include <stdint.h>
#include <stdlib.h>
#include "spec.h"
#include MBYTE_UTF8_C

int nondet_int(void);
size_t nondet_size(void);

// Reference: the codepoint around p is a lead byte at most 5 bytes back (and not
// before base) followed by exactly the continuation bytes it announces, all
// within p_len bytes from p. Then the result is (bytes back to the lead, bytes
// to one past the end). Anything else (ASCII at p, no lead found, a sequence
// that ends before p, one cut off by p_len, a missing continuation byte) gives
// (0, 1).
static void ref_bounds(const uint8_t *base, const uint8_t *p, int p_len, int *b, int *e) {
  *b = 0; *e = 1;
  if (!spec_is_cont(p[0]) && p[0] < 0x80) return;
  size_t back = (size_t)(p - base);
  size_t k = 0;
  while (spec_is_cont(p[-(ptrdiff_t)k])) {   // walk back over continuation bytes
    if (k == back || k == 5) return;          // reached base, or more than 5 back
    k++;
  }
  int L = spec_lead_len(p[-(ptrdiff_t)k]);
  if ((size_t)L <= k || (long)L - (long)k > p_len) return;
  for (int j = 1; j < L; j++) if (!spec_is_cont(p[j - (ptrdiff_t)k])) return;
  *b = (int)k; *e = L - (int)k;
}

// p is d bytes after base; the object holds base..p
// and then exactly min(p_len, 6) bytes from p (the function may read p[0..p_len-1],
// and never needs more than 6 of them).
void h_cp_bounds_len(void) {
  size_t d = nondet_size();
  int p_len = nondet_int();
  __CPROVER_assume(p_len > 0);                     // documented: assert(p_len > 0)
  size_t ahead = p_len < 6 ? (size_t)p_len : 6;
#ifndef NVIM_FIXED_CP_BOUNDS
  __CPROVER_assume(d <= INT_MAX);   // upstream is wrong past this (findings/cp-bounds-over-2gib.md)
#else
  // Any distance below 2^60. run_cbmc.sh uses --object-bits 3 (61 offset bits)
  // for these harnesses, and the assertion below checks that p really is d bytes
  // past base in CBMC's pointer model (with the default 56 bits it would wrap).
  __CPROVER_assume(d < ((size_t)1 << 60) - 6);
#endif
  uint8_t *obj = malloc(d + ahead);
  const char *base = (const char *)obj, *p = (const char *)obj + d;
  __CPROVER_assert((size_t)(p - base) == d, "pointer model holds distance d");
  CharBoundsOff r = utf_cp_bounds_len(base, p, p_len);
  int b, e; ref_bounds(obj, obj + d, p_len, &b, &e);
  __CPROVER_assert(r.begin_off == b && r.end_off == e, "cp_bounds_len");
}

// utf_cp_bounds(base, p) = utf_cp_bounds_len(base, p, INT_MAX) on a NUL-terminated
// stream: the object is base..p, then a string of n bytes (n <= 5) and its NUL, or
// 6 nonzero bytes for longer strings (never read past, as above). The reference
// gets the real number of bytes from p, so it agrees with p_len = INT_MAX exactly
// when nothing past the NUL matters.
void h_cp_bounds(void) {
  size_t d = nondet_size();
#ifndef NVIM_FIXED_CP_BOUNDS
  __CPROVER_assume(d <= INT_MAX);
#else
  __CPROVER_assume(d < ((size_t)1 << 60) - 7);   // see h_cp_bounds_len
#endif
  int n = nondet_int();
  __CPROVER_assume(0 <= n && n <= 6);
  size_t ahead = n < 6 ? (size_t)n + 1 : 6;     // n bytes + NUL, or 6 nonzero bytes
  uint8_t *obj = malloc(d + ahead);
  for (int i = 0; i < n && i < 6; i++) __CPROVER_assume(obj[d + i] != 0);
  if (n < 6) obj[d + n] = 0;
  __CPROVER_assert((size_t)((obj + d) - obj) == d, "pointer model holds distance d");
  CharBoundsOff r = utf_cp_bounds((const char *)obj, (const char *)obj + d);
  int b, e; ref_bounds(obj, obj + d, INT_MAX, &b, &e);
  __CPROVER_assert(r.begin_off == b && r.end_off == e, "cp_bounds");
}
