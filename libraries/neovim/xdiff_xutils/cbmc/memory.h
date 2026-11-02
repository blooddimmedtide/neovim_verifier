// Stand-in for src/nvim/memory.h, which src/xdiff/xdiff.h includes for xmalloc / xfree.
// Neovim's xmalloc never returns NULL (it exits on out-of-memory); this model may also
// return NULL, which is more general: the xdiff code checks for it. A fresh object of
// exactly the size asked for, so any access past it fails --pointer-check.
#include <stddef.h>
#include <stdbool.h>
bool nondet_bool(void);
static int n_free; static void *freed[4];
static void *xmalloc(size_t n) {
  if (n > ((size_t)1 << 50) || nondet_bool()) return NULL;
  return __CPROVER_allocate(n, 0);
}
static void xfree(void *p) { if (n_free < 4) freed[n_free] = p; n_free++; }
static void *xcalloc(size_t a, size_t b) { (void)a; (void)b; __CPROVER_assert(0, "not used"); return NULL; }
static void *xrealloc(void *p, size_t n) { (void)p; (void)n; __CPROVER_assert(0, "not used"); return NULL; }
