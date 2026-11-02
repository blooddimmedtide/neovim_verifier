// Allocation model for the strbuf proofs. The harness defines malloc, realloc,
// free and abort itself (the code under test is not changed):
//  - malloc / realloc may fail (return NULL) on any call, and always fail above
//    MAX_OBJ bytes (CBMC's object limit; real allocators fail far earlier, at
//    PTRDIFF_MAX). Otherwise they return a fresh object of exactly the size
//    asked for, so any access past it fails --pointer-check.
//  - realloc keeps the first min(old, new) bytes (checked at a nondeterministic
//    index by the harnesses) and does not free the old block (leaks are not
//    checked here).
//  - free records each pointer it is given.
//  - abort checks that dying is allowed in the current harness (die_ok), then
//    ends the path: abort does not return.
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
static bool (*die_ok)(void);   // set by each harness: may the code die now?
void *malloc(size_t n) {
  if (n > MAX_OBJ || nondet_bool()) { alloc_failed = 1; return NULL; }
  n_alloc++;
  return __CPROVER_allocate(n, 0);
}
void *realloc(void *p, size_t n) {
  if (n > MAX_OBJ || nondet_bool()) { alloc_failed = 1; return NULL; }
  char *q = __CPROVER_allocate(n, 0);
  if (p) __CPROVER_array_replace(q, (char *)p);
  n_alloc++;
  return q;
}
void free(void *p) {
  if (n_free < 4) freed[n_free] = p;
  n_free++;
}
void abort(void) {
  __CPROVER_assert(die_ok && die_ok(), "die() only where the spec allows it");
  __CPROVER_assume(0);  // abort does not return
}
static bool was_freed(void *p) {
  for (int i = 0; i < 4 && i < n_free; i++) if (freed[i] == p) return true;
  return false;
}
