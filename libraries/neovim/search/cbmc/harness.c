// CBMC proof of full functional correctness of search.c's set_last_csearch.
//
// Precondition (what every caller gives): len >= 0 and s points to at least
// len readable bytes. The only caller with an unbounded len is setcharsearch(),
// which passes utfc_ptr2len(s): a base character plus any number of composing
// characters.
//
// Postcondition, with n = lastc_bytelen afterwards:
//   1. lastc[0] == (uint8_t)c and lastc[1] is unchanged;
//   2. if len <= MAX_SCHAR_SIZE then n == len;
//      else n is the largest k in 1..MAX_SCHAR_SIZE with s[k] not a UTF-8
//      trail byte, or 0 when there is none: the cut falls on a character
//      boundary, keeping only whole characters;
//   3. lastc_bytes[0..n) == s[0..n) and lastc_bytes[n..MAX_SCHAR_SIZE] are all
//      NUL, so the result is a NUL-terminated string with nothing left from an
//      earlier character;
//   4. no out-of-bounds access, overflow or undefined behaviour (CBMC checks).
// lastc_bytes starts with arbitrary contents, so (3) covers stale bytes.
#include <stdlib.h>
#include SEARCH_C

int nondet_int(void);
char nondet_char(void);
uint8_t nondet_u8(void);

static bool is_trail(char b) { return ((uint8_t)b & 0xC0) == 0x80; }

void h_set_last_csearch(void)
{
  int c = nondet_int();
  int len = nondet_int();
  __CPROVER_assume(len >= 0 && len <= MAXLEN);
  char *s = malloc((size_t)len);   // exactly len readable bytes
  for (int i = 0; i < MAX_SCHAR_SIZE + 1; i++) {
    lastc_bytes[i] = nondet_char();
  }
  lastc[1] = nondet_u8();
  uint8_t old1 = lastc[1];

  set_last_csearch(c, s, len);

  int n = lastc_bytelen;
  __CPROVER_assert(lastc[0] == (uint8_t)c, "lastc[0] is c");
  __CPROVER_assert(lastc[1] == old1, "lastc[1] unchanged");
  if (len <= MAX_SCHAR_SIZE) {
    __CPROVER_assert(n == len, "short char kept whole");
  } else {
    __CPROVER_assert(n >= 0 && n <= MAX_SCHAR_SIZE, "cut length in range");
    __CPROVER_assert(n == 0 || !is_trail(s[n]), "cut on a character boundary");
    for (int k = n + 1; k <= MAX_SCHAR_SIZE; k++) {
      __CPROVER_assert(is_trail(s[k]), "longest cut");
    }
  }
  for (int i = 0; i < MAX_SCHAR_SIZE + 1; i++) {
    if (i < n) {
      __CPROVER_assert(lastc_bytes[i] == s[i], "bytes copied");
    } else {
      __CPROVER_assert(lastc_bytes[i] == NUL, "tail cleared");
    }
  }
}
