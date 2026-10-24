#pragma once
#include <stdlib.h>
// Neovim's xmalloc never returns NULL (it exits on OOM), so model it that way.
static inline void *xmalloc(size_t n) {
  void *p = malloc(n);
  __CPROVER_assume(p != NULL);
  return p;
}
static inline void xfree(void *p) { free(p); }
