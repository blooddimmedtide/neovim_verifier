// Reproducer for str2nr-over-2gib.md.
// Build: python3 -I ../charset/wp/build.py <nvim> cs.c   (add --fixed for the fork)
//        grep -v 'vp_string.h\|nvim/memory.h' cs.c > cs_real.c
//        gcc -O1 -g -fsanitize=undefined -DCS_C=\"cs_real.c\" str2nr-over-2gib-repro.c
// Run:   ./a.out d   decimal digits, 2^31 + 16 of them: upstream reports a negative length
//        ./a.out o   "0" + 2^31 + 16 octal digits: UBSan reports the 'int i' overflow
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
void *xmalloc(size_t n) { void *p = malloc(n ? n : 1); if (!p) abort(); return p; }
char *xstrchrnul(const char *str, char c) { while (*str && *str != c) str++; return (char *)str; }
#include CS_C
int main(int argc, char **argv) {
  size_t n = ((size_t)1 << 31) + 16;
  char *s = malloc(n + 2);
  if (!s) { perror("malloc"); return 2; }
  if (argc > 1 && argv[1][0] == 'o') { s[0] = '0'; memset(s + 1, '7', n); s[n + 1] = 0; }
  else { memset(s, '1', n); s[n] = 0; }
  int len = 12345; varnumber_T v = 0;
  vim_str2nr(s, NULL, &len, STR2NR_ALL, &v, NULL, 0, false, NULL);
  printf("characters=%zu len=%d value=%lld\n", strlen(s), len, (long long)v);
  return 0;
}
