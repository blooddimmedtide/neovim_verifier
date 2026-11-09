// Contracts for what the typeahead/stuff buffer functions of input.c call outside
// themselves. Everything here is trusted (listed in ../CLAIM.md); no axioms.
#ifndef VP_TYPEBUF_H
#define VP_TYPEBUF_H
#include <stddef.h>
#include <stdint.h>
#include <limits.h>
#include "vp_string.h"

/*@ ghost long vp_live; */      // live allocations
/*@ ghost int vp_oom; */        // allocations may run out of memory (then preserve_exit())

/*@ // xmalloc (memory.c): never returns NULL; exits when memory runs out
    requires n > 0;
    requires vp_live < LONG_MAX;
    assigns \result \from n;
    assigns vp_live;
    allocates \result;
    ensures \result != \null && \fresh{Old, Here}((char *)\result, n);
    ensures vp_live == \old(vp_live) + 1;
    exits vp_oom;
*/
void *xmalloc(size_t n);

/*@ // xrealloc (memory.c): the bytes of p that are in range are kept
    requires n > 0;
    requires vp_live < LONG_MAX;
    assigns \result \from p, n;
    assigns vp_live;
    allocates \result;
    ensures \result != \null && \valid((char *)\result + (0 .. n - 1));
    ensures \forall integer i; 0 <= i < n && p != \null && \at(\valid_read((char *)p + i), Pre) ==>
              ((char *)\result)[i] == \old(((char *)p)[i]);
    // the same block, or a new one
    ensures (p != \null && \base_addr((char *)\result) == \base_addr((char *)p)) || \fresh{Old, Here}((char *)\result, n);
    ensures vp_live == \old(vp_live) + (p == \null ? 1 : 0);
    exits vp_oom;
*/
void *xrealloc(void *p, size_t n);

/*@ requires p != \null ==> vp_live > LONG_MIN;
    assigns vp_live;
    ensures vp_live == \old(vp_live) - (p == \null ? 0 : 1);
*/
void xfree(void *p);

/*@ assigns \nothing; */
void state_no_longer_safe(const char *reason);
/*@ assigns \nothing; */
void internal_error(const char *where);
/*@ assigns \nothing; */
void setcursor(void);
#endif
