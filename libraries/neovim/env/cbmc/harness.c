// CBMC harnesses for vim_env_iter / vim_env_iter_rev. Every string of length <= N over
// every byte value, every delimiter, exact-size objects (out-of-bounds reads fail).
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#define FUNC_ATTR_NONNULL_ARG(...)
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_PURE
#include ENV_C
#ifndef N
#define N 5
#endif
size_t nondet_size(void); char nondet_char(void);

static char *mkstr(size_t *np) {
  size_t n = nondet_size(); __CPROVER_assume(n <= N);
  char *s = malloc(n + 1);
  for (size_t i = 0; i < n; i++) { s[i] = nondet_char(); __CPROVER_assume(s[i] != 0); }
  s[n] = 0; *np = n; return s;
}

// Reference (written from the doc): the list "a<d>b<d>c" has items a, b, c; an empty
// string has one empty item. Forward iteration must return exactly these items in order.
void h_iter(void) {
  size_t n; char *val = mkstr(&n); char d = nondet_char(); __CPROVER_assume(d != 0);
  const void *it = NULL; size_t start = 0; size_t items = 0;
  do {
    const char *dir; size_t len;
    it = vim_env_iter(d, val, it, &dir, &len);
    // reference item: from start to next d or end
    size_t e = start; while (e < n && val[e] != d) e++;
    __CPROVER_assert(dir == val + start, "item start");
    __CPROVER_assert(len == e - start, "item length");
    __CPROVER_assert((it == NULL) == (e == n), "stops exactly after last item");
    if (it) __CPROVER_assert(it == val + e + 1, "next iter");
    start = e + 1; items++;
  } while (it != NULL);
  free(val);
}

// Reverse iteration must return the same items, last first.
void h_iter_rev(void) {
  size_t n; char *val = mkstr(&n); char d = nondet_char(); __CPROVER_assume(d != 0);
  const void *it = NULL; size_t end = n;  // reference: current item ends before `end`
  do {
    const char *dir; size_t len;
    it = vim_env_iter_rev(d, val, it, &dir, &len);
    size_t b = end; while (b > 0 && val[b - 1] != d) b--;
    __CPROVER_assert(dir == val + b, "item start");
    __CPROVER_assert(len == end - b, "item length");
    __CPROVER_assert((it == NULL) == (b == 0), "stops exactly after first item");
    if (b == 0) break;
    end = b - 1;
  } while (it != NULL);
  free(val);
}
