/* Independent references, written from the doc comments of linematch.c (not its code). */
#include <stddef.h>
/* line_len: length of the first line of m: bytes before the first '\n' in
   ptr[0..size), or size if there is none. */
static size_t ref_line_len(const char *p, int size) {
  for (int i = 0; i < size; i++) if (p[i] == '\n') return (size_t)i;
  return (size_t)size;
}
/* Longest common subsequence length (the doc's "matching characters whilst
   respecting sequence order"), by plain recursion over the definition. */
static int ref_lcs(const char *a, int n, const char *b, int m) {
  if (n == 0 || m == 0) return 0;
  if (a[n - 1] == b[m - 1]) return ref_lcs(a, n - 1, b, m - 1) + 1;
  int x = ref_lcs(a, n - 1, b, m), y = ref_lcs(a, n, b, m - 1);
  return x > y ? x : y;
}
