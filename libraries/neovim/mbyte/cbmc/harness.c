// CBMC proofs of full functional correctness of the UTF-8 helpers in
// src/nvim/mbyte.c, for every input. Inputs are nondeterministic (CBMC treats
// every value at once); loops are bounded and --unwinding-assertions proves
// the bound is enough, so each check covers all inputs, not samples.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "spec.h"
#include MBYTE_UTF8_C   // build.py output: verbatim upstream functions

int nondet_int(void);
size_t nondet_size(void);

// utf_byte2len: for every b in 0..255, the length the lead byte announces.
void h_byte2len(void) {
  int b = nondet_int();
  __CPROVER_assume(0 <= b && b <= 255);   // documented domain ("must be between 0 and 255")
  __CPROVER_assert(utf_byte2len(b) == spec_lead_len((uint8_t)b), "byte2len = lead length");
}

// utf_char2len: for c < 0, 1; otherwise the shortest encoding length.
void h_char2len(void) {
  int c = nondet_int();
  int r = utf_char2len(c);
  if (c < 0) __CPROVER_assert(r == 1, "negative -> 1");
  else __CPROVER_assert(r == spec_enc_len(c), "shortest encoding length");
}

// utf_char2bytes: writes exactly the shortest well-formed encoding of c and
// nothing else; for c < 0 writes the low byte of c (documented as 1 byte).
void h_char2bytes(void) {
  int c = nondet_int();
  char buf[8];
  char before[8];
  for (int i = 0; i < 8; i++) before[i] = buf[i];
  int r = utf_char2bytes(c, buf);   // buf is 8 bytes; the check below shows only buf[0..r-1] change
  const uint8_t *u = (const uint8_t *)buf;
  for (int i = r; i < 8; i++) __CPROVER_assert(buf[i] == before[i], "bytes past the result untouched");
  if (c < 0) {
    __CPROVER_assert(r == 1 && u[0] == (uint8_t)(uint32_t)c, "negative: one byte, low 8 bits");
    return;
  }
  __CPROVER_assert(r == spec_enc_len(c), "length is the shortest encoding");
  __CPROVER_assert(spec_lead_len(u[0]) == r && (r > 1 || u[0] < 0x80), "lead byte announces the length");
  for (int k = 1; k < r; k++) __CPROVER_assert(spec_is_cont(u[k]), "continuation bytes");
  __CPROVER_assert(spec_value(u, r) == (uint32_t)c, "decodes back to c");
}

// A NUL-terminated string of length n (0..max) in an object of exactly n+1
// bytes, so any read past the terminator fails the pointer check. Longer
// strings are covered by the *_long harnesses below.
static char *any_str(int max, int *len) {
  int n = nondet_int();
  __CPROVER_assume(0 <= n && n <= max);
  char *s = malloc((size_t)n + 1);
  for (int i = 0; i < n; i++) __CPROVER_assume(s[i] != 0);
  s[n] = 0;
  *len = n;
  return s;
}



// Strings of length 0..6: exact objects, so reads past the NUL are caught.
void h_ptr2len(void) {
  int n; char *s = any_str(6, &n);
  __CPROVER_assert(utf_ptr2len(s) == ref_ptr2len((const uint8_t *)s), "ptr2len");
}
void h_ptr2char(void) {
  int n; char *s = any_str(6, &n);
  __CPROVER_assert(utf_ptr2char(s) == ref_ptr2char((const uint8_t *)s), "ptr2char");
}
// Strings of length 7 or more: their first 6 bytes are nonzero. Give the
// functions an object of exactly 6 nonzero bytes: the pointer check proves they
// never read index 6 or beyond, so their result depends only on those 6 bytes
// and holds for every longer string with the same prefix.
void h_ptr2len_long(void) {
  char *s = malloc(6);
  for (int i = 0; i < 6; i++) __CPROVER_assume(s[i] != 0);
  __CPROVER_assert(utf_ptr2len(s) == ref_ptr2len((const uint8_t *)s), "ptr2len (long)");
}
void h_ptr2char_long(void) {
  char *s = malloc(6);
  for (int i = 0; i < 6; i++) __CPROVER_assume(s[i] != 0);
  __CPROVER_assert(utf_ptr2char(s) == ref_ptr2char((const uint8_t *)s), "ptr2char (long)");
}

// Any size (also <= 0), with an object of exactly max(size, 1) bytes: the
// function always reads p[0], and the pointer check shows it reads nothing
// past p[size-1] otherwise. For size > 6 only 6 bytes can matter (proved the
// same way as above: the object is 6 bytes and size is anything >= 6).
void h_ptr2len_len(void) {
  int size = nondet_int();
  int obj = size < 1 ? 1 : size > 6 ? 6 : size;
  char *p = malloc((size_t)obj);
  __CPROVER_assert(utf_ptr2len_len(p, size) == ref_ptr2len_len((const uint8_t *)p, size), "ptr2len_len");
}
