#pragma once
#include <stddef.h>
// Contract for Neovim's xmalloc (src/nvim/memory.c): it allocates max(n, 1)
// bytes and never returns NULL (preserve_exit() on out-of-memory).
//
// WP does not model allocation state (it ignores \fresh, \freeable and frees),
// so two ghost variables track it instead: vp_live counts live allocations
// and vp_last is the most recent one. xfree may only free vp_last, once.
// (Copy of libraries/neovim/base64/wp/stubs/nvim/memory.h plus the spelled-out \fresh below.)
// This makes a leak, a double free, freeing the wrong pointer, or returning
// a freed buffer fail the proof.
/*@ ghost int vp_live; */
/*@ ghost void *vp_last; */

/*@ requires vp_live < 2147483647;
    requires \valid_read(avoid + (0 .. avoid_len - 1));
    assigns \result \from n;
    assigns vp_live, vp_last;
    allocates \result;
    ensures \result != \null;
    ensures \valid((char *)\result + (0 .. n - 1));
    ensures \fresh(\result, n);
    // \fresh spelled out for one live object the caller names (WP ignores \fresh):
    // the new block does not overlap avoid[0 .. avoid_len - 1], which is readable at the call.
    // True of any allocator: a new block never overlaps a live object.
    ensures \separated((char *)\result + (0 .. n - 1), avoid + (0 .. avoid_len - 1));
    ensures \base_addr(\result) != \base_addr(avoid);   // a new object
    ensures vp_live == \old(vp_live) + 1 && vp_last == \result;
*/
void *xmalloc(size_t n) /*@ ghost (char *avoid, size_t avoid_len) */;

/*@ requires vp_live >= 1 && p == vp_last && p != \null;
    assigns vp_live, vp_last;
    ensures vp_live == \old(vp_live) - 1 && vp_last == \null;
*/
void xfree(void *p);
