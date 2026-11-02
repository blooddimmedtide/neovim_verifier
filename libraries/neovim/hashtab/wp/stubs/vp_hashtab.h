// Contracts for what hashtab.c calls outside itself. Everything here is trusted
// (listed in ../CLAIM.md); no axioms are used.
#ifndef VP_HASHTAB_H
#define VP_HASHTAB_H
#include <stddef.h>
#include <stdint.h>
#include <limits.h>
#include "vp_string.h"

// Allocation state, as in ../../garray/wp/stubs/vp_garray.h: vp_live counts live
// allocations; every xfree call is logged in order in vp_freelog[0 .. vp_nfree - 1].
/*@ ghost long vp_live; */
/*@ ghost size_t vp_nfree; */
// vp_oom: whether an allocation may run out of memory (memory.c then calls
// preserve_exit()). Never assigned: "exits vp_oom || <cond>" states exactly when a
// function exits.
/*@ ghost int vp_oom; */
/*@ ghost void *vp_freelog[4294967296]; */

/*@ requires vp_nfree < 4294967296;
    requires p != \null ==> vp_live > LONG_MIN;
    assigns vp_live, vp_nfree, vp_freelog[vp_nfree];
    ensures vp_nfree == \old(vp_nfree) + 1 && vp_freelog[\old(vp_nfree)] == p;
    ensures vp_live == \old(vp_live) - (p == \null ? 0 : 1);
*/
void xfree(void *p);

/*@ // siemsg (message.c): reports an internal error; changes nothing hashtab.c reads
    assigns \nothing; */
void siemsg(const char *s, ...);
#endif
