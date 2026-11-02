// CBMC proofs of full functional correctness of regexp.c's gethexchrs and
// getoctchrs, for every input. The input object holds exactly the bytes the
// function may read, with arbitrary contents (NUL included), so a read past them
// fails the pointer check.
#include <stdint.h>
#include <stdlib.h>
#include "spec.h"
#include REGEXP_NUM_C   // build.py output: verbatim upstream functions

int nondet_int(void);

// gethexchrs(max): reads the longest run of at most max hex digits; returns its
// value and moves regparse past it, or returns -1 and leaves regparse when the
// first byte is not a hex digit. Callers pass max = 2, 4 or 8.
void h_gethexchrs(void) {
  int max = nondet_int();
  __CPROVER_assume(max == 2 || max == 4 || max == 8);   // the callers' values
  char *buf = malloc((size_t)max);                      // any bytes
  regparse = buf;
  int64_t r = gethexchrs(max);
  int n = 0;
  int64_t v = 0;
  while (n < max && spec_hexdigit((unsigned char)buf[n]) >= 0) {
    v = v * 16 + spec_hexdigit((unsigned char)buf[n]);
    n++;
  }
  if (n == 0) {
    __CPROVER_assert(r == -1 && regparse == buf, "no digit: -1, nothing consumed");
  } else {
    __CPROVER_assert(r == v, "value of the digits");
    __CPROVER_assert(regparse == buf + n, "consumed exactly the digits");
  }
}

// getoctchrs(): reads the longest run of at most 3 octal digits whose value is
// at most 0377; returns its value and moves past it, or -1 when the first byte
// is not an octal digit.
void h_getoctchrs(void) {
  char *buf = malloc(3);   // any bytes
  regparse = buf;
  int64_t r = getoctchrs();
  int n = 0;
  int64_t v = 0;
  while (n < 3 && spec_octdigit((unsigned char)buf[n]) >= 0
         && v * 8 + spec_octdigit((unsigned char)buf[n]) <= 0377) {
    v = v * 8 + spec_octdigit((unsigned char)buf[n]);
    n++;
  }
  if (n == 0) {
    __CPROVER_assert(r == -1 && regparse == buf, "no digit: -1, nothing consumed");
  } else {
    __CPROVER_assert(r == v && 0 <= r && r <= 0377, "value of the digits, at most 0377");
    __CPROVER_assert(regparse == buf + n, "consumed exactly the digits");
  }
}
