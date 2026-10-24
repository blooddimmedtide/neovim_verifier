#pragma once
#include <stdio.h>
#include <stdlib.h>
// Native build: same contract as Neovim's xmalloc (never NULL, max(n,1) bytes).
static inline void *xmalloc(size_t n) {
  void *p = malloc(n ? n : 1);
  if (!p) { fputs("out of memory\n", stderr); exit(2); }
  return p;
}
static inline void xfree(void *p) { free(p); }
