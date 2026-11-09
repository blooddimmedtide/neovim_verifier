// Differential test: compiled upstream code (gcc -O2, real libc) against the
// spec.h references, exhaustive over a small alphabet for lengths 0..7.
// Build: python3 -I build.py <nvim> tag_extract.c && gcc -O2 -fsigned-char -DNV_REAL_LIBC difftest.c && ./a.out
#include "tag_extract.c"
#include "spec.h"
#include <stdio.h>
static const char AL[] = {'\t', 'f', 'i', 'l', 'e', ':', 'a', 'Z'};
#define A 8
static long fails;
static void check(char *s, size_t sl)
{
  tagptrs_T t; int r = parse_tag_line(s, &t);
  size_t t1 = spec_index_of(s, 0, sl + 1, TAB);
  size_t t2 = t1 < sl ? spec_index_of(s, t1 + 1, sl + 1, TAB) : sl + 1;
  int ok = t1 < sl && t2 < sl && s[t2 + 1] != NUL;
  if (r != (ok ? OK : FAIL) || (ok && t.command != s + t2 + 1)) fails++;
  for (size_t off = 0; off <= sl; off++) {
    t.command = s + off; int w = 0;
    for (size_t i = off; i + 5 < sl + 1; i++)
      if (s[i] == '\t' && !memcmp(s + i + 1, "file:", 5)) w = 1;
    if (test_for_static(&t) != w) fails++;
  }
}
int main(void)
{
  char s[9]; long n = 0;
  for (int len = 0; len <= 7; len++) {
    long tot = 1; for (int i = 0; i < len; i++) tot *= A;
    for (long k = 0; k < tot; k++) {
      long x = k; for (int i = 0; i < len; i++) { s[i] = AL[x % A]; x /= A; }
      s[len] = 0; check(s, (size_t)len); n++;
    }
  }
  const char *w[] = {"", "a", "A", "ab", "AB", "aB", "b", "~", "`", "{", "@", "[", "\xe9", "\xc9"};
  for (int i = 0; i < 14; i++) for (int j = 0; j < 14; j++) for (size_t l = 0; l < 4; l++) {
    int r = tag_strnicmp((char *)w[i], (char *)w[j], l), want = 0;
    for (size_t q = 0; q < l; q++) { int d = spec_upper((unsigned char)w[i][q]) - spec_upper((unsigned char)w[j][q]);
      if (d) { want = d; break; } if (!w[i][q]) break; }
    if (r != want) fails++;
  }
  printf("difftest: %ld lines, %ld failures\n", n, fails);
  return fails != 0;
}
