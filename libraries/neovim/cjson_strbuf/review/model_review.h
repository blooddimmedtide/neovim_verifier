// Allocation model for the reviewer's strengthened harness (harness_review.c).
// Same as ../cbmc/model.h except that free() and realloc() END the lifetime of
// the block they release (__CPROVER_deallocate), so --pointer-check reports any
// later use of it (use after free, use of the pre-realloc pointer).
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
bool nondet_bool(void);
size_t nondet_size(void);
int nondet_int(void);
char nondet_char(void);
#define MAX_OBJ ((size_t)1 << 50)
static int n_alloc, n_free, alloc_failed;
static void *freed[4];
static bool (*die_ok)(void);
void *malloc(size_t n) {
  if (n > MAX_OBJ || nondet_bool()) { alloc_failed = 1; return NULL; }
  n_alloc++;
  return __CPROVER_allocate(n, 0);
}
void *realloc(void *p, size_t n) {
  if (n > MAX_OBJ || nondet_bool()) { alloc_failed = 1; return NULL; }
  char *q = __CPROVER_allocate(n, 0);
  if (p) { __CPROVER_array_replace(q, (char *)p); __CPROVER_deallocate(p); }
  n_alloc++;
  return q;
}
void free(void *p) {
  if (n_free < 4) freed[n_free] = p;
  n_free++;
  if (p) __CPROVER_deallocate(p);
}
void abort(void) {
  __CPROVER_assert(die_ok && die_ok(), "die() only where the spec allows it");
  __CPROVER_assume(0);
}
static bool was_freed(void *p) {
  for (int i = 0; i < 4 && i < n_free; i++) if (freed[i] == p) return true;
  return false;
}
