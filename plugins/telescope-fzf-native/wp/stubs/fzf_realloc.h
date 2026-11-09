// realloc for the WP proof of fzf.c. Every realloc call in fzf.c is
// `(uint32_t *)realloc(pos->data, sizeof(uint32_t) * pos->cap)`, so the model is
// stated on uint32_t elements (C11 7.22.3.5): the result is a block of n bytes
// whose first elements are the old block's, up to the smaller of the two sizes
// (an element of the old block is one that was readable before the call).
// Allocation never fails (the code never tests the result). WP's Typed model keeps
// uint32_t memory apart from char and size_t memory, so the new block cannot
// overlap the text, the pattern or the position struct; Frama-C WP does not
// implement \fresh, so nothing more is claimed about it. No axiomatic definitions.
#ifndef FZF_REALLOC_H
#define FZF_REALLOC_H
#include <stddef.h>
#include <stdint.h>
/*@ requires n % 4 == 0;
    assigns \result \from p, n;
    ensures \valid(\result + (0 .. n / 4 - 1));
    ensures \forall integer i; 0 <= i < n / 4 && \at(\valid_read(p + i), Pre)
              ==> \result[i] == \at(p[i], Pre); */
uint32_t *fzf_realloc(uint32_t *p, size_t n);   // typed: the cast (uint32_t *) is then the identity
#define realloc fzf_realloc
#endif
