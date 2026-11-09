// Shared harness helper. CBMC 6.4.1's SAT encoding runs out of memory (> 6 GB)
// on dynamic objects whose size is a symbolic expression once realloc is
// involved, so every harness object of nondeterministic length is allocated
// with a constant size in one branch per possible length. The result is the
// same set of objects (exactly n elements, n <= max).
#ifndef FZF_HARNESS_UTIL_H
#define FZF_HARNESS_UTIL_H
#include <stdlib.h>
static void *exact_malloc(size_t n, size_t max, size_t elem) {
  __CPROVER_assume(n <= max);
  void *p = NULL;
  for (size_t k = 0; k <= max; k++)
    if (n == k) p = malloc(k * elem);
  return p;
}
// malloc as fzf.c sees it. CBMC runs out of memory when the code under test
// mallocs symbolic sizes on paths it cannot rule out, so (both sound):
//  - CODE_MALLOC_UNREACHABLE: fzf.c must not call malloc at all (asserted);
//    used with a slab big enough for every buffer.
//  - CODE_MALLOC_MAX=k: sizes up to k bytes (asserted), each in a branch with
//    a constant size (the same object CBMC's malloc would give).
#if defined(CODE_MALLOC_UNREACHABLE)
void *fzfv_code_malloc(size_t n) {
  __CPROVER_assert(0, "fzf.c does not call malloc in this harness");
  __CPROVER_assume(0);
  return NULL;
}
#define FZFV_CODE_MALLOC 1
#elif defined(CODE_MALLOC_MAX)
void *fzfv_code_malloc(size_t n) {
  __CPROVER_assert(n <= CODE_MALLOC_MAX, "malloc size within the model's bound");
  __CPROVER_assume(n <= CODE_MALLOC_MAX);
  void *p = NULL;
  for (size_t k = 0; k <= CODE_MALLOC_MAX; k++)
    if (n == k) p = malloc(k);
  return p;
}
#define FZFV_CODE_MALLOC 1
#endif
#endif
