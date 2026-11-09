// Contracts for the mbyte.c functions path.c's proved functions call, written
// from its doc comment in src/nvim/mbyte.c ("Return the number of bytes occupied by
// a UTF-8 character in a string. This includes following composing characters.
// Returns zero for NUL."). It is not proved here; CLAIM.md lists it as relied on.
#ifndef VP_PATH_H
#define VP_PATH_H
#include "vp_string.h"
/*@ requires is_str((char *)p);
    assigns \result \from ((char *)p)[0 ..];
    ensures \forall integer m; str_len((char *)p, m) ==>
              (m == 0 ==> \result == 0) && (m > 0 ==> 1 <= \result <= m); */
int utfc_ptr2len(const char *const p);
// utf_head_off (mbyte.c): "Return offset from p to the start of a character, including
// composing characters ... Returns 0 when already at the first byte of a character."
// An ASCII byte is always the first byte of a character (UTF-8, RFC 3629 section 3).
/*@ requires \valid_read(p_in);
    assigns \result \from base_in[0 ..], p_in[0 ..];
    ensures 0 <= \result;
    ensures (unsigned char)*p_in < 0x80 ==> \result == 0; */
int utf_head_off(const char *base_in, const char *p_in);
#endif
