// Differential test: compiled getdecchrs / gethexchrs / getoctchrs (gcc -O2) against
// the reference in ../cbmc/spec.h, exhaustively over every string of up to 4 bytes from
// an alphabet that covers each digit class edge, plus long digit runs for getdecchrs.
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include "../cbmc/spec.h"
#include REGEXP_NUM_C   // build.py output, with getdecchrs appended

static const char ALPHA[] = "0179afAFgG/:@`\x80\xff";
static long fails = 0, checks = 0;

static int64_t ref_dec(const char *s, int *n) {   // min(value, INT_MAX + 1), or -1
  __int128 v = 0; int k = 0;
  while (s[k] >= '0' && s[k] <= '9') { if (v <= INT_MAX) v = v * 10 + (s[k] - '0'); k++; }
  *n = k;
  if (k == 0) return -1;
  return v > INT_MAX ? (int64_t)INT_MAX + 1 : (int64_t)v;
}

static void check(const char *s) {
  for (int max = 2; max <= 8; max *= 2) {
    regparse = (char *)s; int64_t r = gethexchrs(max);
    int n = 0; int64_t v = 0;
    while (n < max && spec_hexdigit((unsigned char)s[n]) >= 0) { v = v * 16 + spec_hexdigit((unsigned char)s[n]); n++; }
    checks++;
    if ((n == 0 ? r != -1 || regparse != s : r != v || regparse != s + n)) { fails++; printf("hex %d [%s]\n", max, s); }
  }
  regparse = (char *)s; int64_t r = getoctchrs();
  int n = 0; int64_t v = 0;
  while (n < 3 && spec_octdigit((unsigned char)s[n]) >= 0 && v * 8 + spec_octdigit((unsigned char)s[n]) <= 0377) { v = v * 8 + spec_octdigit((unsigned char)s[n]); n++; }
  checks++;
  if ((n == 0 ? r != -1 || regparse != s : r != v || regparse != s + n)) { fails++; printf("oct [%s]\n", s); }
#ifdef HAVE_DEC
  curchr = 7; regparse = (char *)s; r = getdecchrs();
  int64_t want = ref_dec(s, &n);
  checks++;
  if (r != want || regparse != s + n || curchr != (n ? -1 : 7)) { fails++; printf("dec [%s]\n", s); }
#endif
}

int main(void) {
  char s[8];
  int A = (int)strlen(ALPHA);
  for (int len = 0; len <= 4; len++) {
    long total = 1; for (int i = 0; i < len; i++) total *= A;
    for (long x = 0; x < total; x++) {
      long y = x;
      for (int i = 0; i < len; i++) { s[i] = ALPHA[y % A]; y /= A; }
      s[len] = 0;
      check(s);
    }
  }
#ifdef HAVE_DEC
  static char big[64];   // long runs around the int and int64 limits
  for (int len = 1; len < 40; len++) for (int d = 0; d < 10; d++) {
    memset(big, '0' + d, (size_t)len); big[len] = 'x'; big[len + 1] = 0; check(big);
  }
  const char *edge[] = { "2147483647x", "2147483648x", "9223372036854775807", "9223372036854775808",
                         "18446744073709551681", "000000000000000000000000000001" };
  for (unsigned i = 0; i < sizeof edge / sizeof *edge; i++) check(edge[i]);
#endif
  printf("%ld checks, %ld mismatches\n", checks, fails);
  return fails != 0;
}
