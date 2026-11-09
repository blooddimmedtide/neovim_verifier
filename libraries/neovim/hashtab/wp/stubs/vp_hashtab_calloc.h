// xcalloc as hashtab.c uses it: an array of `count` hashitem_T. Included after the types.
// Trusted: calloc zeroes every byte, and on x86_64 an all-zero pointer is NULL and an
// all-zero size_t is 0, so every item reads as {hi_hash = 0, hi_key = NULL}.
#ifndef VP_HASHTAB_CALLOC_H
#define VP_HASHTAB_CALLOC_H
/*@ // Neovim's xcalloc (memory.c) never returns NULL: on failure, including count * size
    // overflowing, it frees memory, retries, then calls preserve_exit().
    requires size == sizeof(hashitem_T);
    requires vp_live < LONG_MAX;
    requires \valid_read(a1) && \valid_read(a2);
    assigns \result \from count, size;
    assigns vp_live;
    allocates \result;
    exits vp_oom || count * size > SIZE_MAX;
    ensures count * size <= SIZE_MAX;
    ensures \result != \null && \valid((hashitem_T *)\result + (0 .. count - 1));
    ensures \forall integer i; 0 <= i < count ==>
              ((hashitem_T *)\result)[i].hi_key == \null && ((hashitem_T *)\result)[i].hi_hash == 0;
    // the new block overlaps no live one: stated for the live blocks the caller names
    // (WP does not model allocation, so "every block valid before" would be contradictory)
    ensures \base_addr((char *)\result) != \base_addr(a1) && \base_addr((char *)\result) != \base_addr(a2);
    ensures vp_live == \old(vp_live) + 1;
*/
void *xcalloc(size_t count, size_t size) /*@ ghost (char *a1, char *a2) */;
#endif
