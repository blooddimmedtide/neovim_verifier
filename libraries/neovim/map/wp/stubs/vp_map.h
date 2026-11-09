// Contracts for what map.c calls outside itself, and the types it uses as
// map_defs.h defines them (checked against the upstream text by build.py).
// Everything here is trusted and listed in ../CLAIM.md; no axioms are used.
#ifndef VP_MAP_H
#define VP_MAP_H
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <limits.h>

/*@ ghost int vp_oom; */

/*@ // Neovim's xfree: free(NULL) is a no-op.
    assigns \nothing; */
void xfree(void *p);

/*@ // Neovim's xcalloc (memory.c) never returns NULL: on failure, including
    // count * size overflowing, it calls preserve_exit(). Used here for uint32_t buckets.
    requires size == sizeof(uint32_t);
    assigns \result \from count, size;
    allocates \result;
    exits vp_oom || count * size > SIZE_MAX;
    ensures count * size <= SIZE_MAX;
    ensures \result != \null && \valid((uint32_t *)\result + (0 .. count - 1));
    ensures \forall integer i; 0 <= i < count ==> ((uint32_t *)\result)[i] == 0;
    ensures \forall char *q; \at(\valid_read(q), Pre) ==> \base_addr(q) != \base_addr((char *)\result);
*/
void *xcalloc(size_t count, size_t size);

/*@ // xrealloc to n bytes of int keys: keeps the first `old` ints, never returns NULL.
    requires p == \null || \valid((int *)p + (0 .. old - 1));
    assigns \result \from p, n;
    allocates \result;
    exits vp_oom;
    ensures \result != \null && \valid((char *)\result + (0 .. n - 1));
    ensures \forall integer i; 0 <= i < old && i * sizeof(int) < n ==> ((int *)\result)[i] == \old(((int *)p)[i]);
*/
void *xrealloc(void *p, size_t n) /*@ ghost (size_t old) */;

/*@ requires \valid((uint32_t *)d + (0 .. n / sizeof(uint32_t) - 1));
    requires c == 0 && n % sizeof(uint32_t) == 0;
    assigns ((uint32_t *)d)[0 .. n / sizeof(uint32_t) - 1];
    ensures \forall integer i; 0 <= i < n / sizeof(uint32_t) ==> ((uint32_t *)d)[i] == 0;
    ensures \result == d; */
void *memset(void *d, int c, size_t n);

/*@ // abort(): never returns. map.c calls it only when its own invariants are broken.
    assigns \nothing;
    exits \true;
    ensures \false; */
void abort(void);

#endif
