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
    ensures \result != \null && \valid((char *)\result + (0 .. n - 1));
    // a new block: not one of the blocks the caller names (ghost "avoid" arguments;
    // WP does not implement \fresh)
    ensures \base_addr((char *)\result) != \base_addr((char *)a1) && \base_addr((char *)\result) != \base_addr((char *)a2)
            && \base_addr((char *)\result) != \base_addr((char *)a3) && \base_addr((char *)\result) != \base_addr((char *)a4);
    ensures vp_live == \old(vp_live) + 1;
    exits vp_oom;
*/
void *xmalloc(size_t n) /*@ ghost (void *a1, void *a2, void *a3, void *a4) */;

/*@ ghost void *vp_av1; void *vp_av2; */  // blocks the caller names as "not p" before xrealloc
/*@ // xrealloc (memory.c): the bytes of p that are in range are kept
    requires n > 0;
    // the avoid blocks are live and are not p's block, so the result (p's block moved or kept)
    // cannot be either of them. Set by a ghost statement in the caller (kv_resize is a macro, so
    // the call cannot take ghost arguments).
    requires \valid_read((char *)vp_av1) && \valid_read((char *)vp_av2);
    requires p != \null ==> \base_addr((char *)vp_av1) != \base_addr((char *)p) && \base_addr((char *)vp_av2) != \base_addr((char *)p);
    requires vp_live < LONG_MAX;
    assigns \result \from p, n;
    assigns vp_live;
    allocates \result;
    ensures \result != \null && \valid((char *)\result + (0 .. n - 1));
    ensures \base_addr((char *)\result) != \base_addr((char *)vp_av1) && \base_addr((char *)\result) != \base_addr((char *)vp_av2);
    ensures \forall integer i; 0 <= i < n && p != \null && \at(\valid_read((char *)p + i), Pre) ==>
              ((char *)\result)[i] == \old(((char *)p)[i]);
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
