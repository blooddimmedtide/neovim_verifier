// Contracts for what the option-value helpers call outside themselves. Trusted
// (listed in ../CLAIM.md); no axioms.
#ifndef VP_OPTION_H
#define VP_OPTION_H
#include <stddef.h>
#include <stdint.h>
#include "vp_string.h"

/*@ // every byte of the string is ASCII (1 .. 0x7F)
    predicate ascii_str{L}(char *s) = \forall integer n, i; str_len(s, n) && 0 <= i < n ==> (unsigned char)s[i] < 0x80;
*/
/*@ // vim_strchr (strings.c). For 0 < c < 0x80 its body is `return (char *)strchr(string, c);`,
    // so this is the C11 strchr contract from vp_string.h for non-NUL c. For 0x80 <= c <= 0xFF
    // it searches for the UTF-8 encoding of c (utf_char2bytes + strstr); that encoding's lead
    // byte is >= 0xC2, so in an all-ASCII string it is never found.
    requires 0 < c <= 0xFF;
    requires is_str((char *)string);
    requires c >= 0x80 ==> ascii_str((char *)string);
    assigns \result \from string, c, ((char *)string)[0 ..];
    behavior found:
      assumes c < 0x80 && \exists integer n, i; str_len((char *)string, n) && 0 <= i < n && string[i] == (char)c;
      ensures \exists integer i; 0 <= i && \result == string + i && string[i] == (char)c
              && \forall integer j; 0 <= j < i ==> string[j] != (char)c && string[j] != 0;
    behavior not_found:
      assumes c >= 0x80 || \forall integer n, i; str_len((char *)string, n) && 0 <= i < n ==> string[i] != (char)c;
      ensures \result == \null;
    complete behaviors; disjoint behaviors; */
char *vim_strchr(const char *const string, const int c);

typedef struct {
  char *data;
  size_t size;  ///< Total writable bytes, including any space for a terminating NUL.
} CharBuf;

// transchar() (charset.c) writes its static transchar_charbuf; this ghost stands for it.
/*@ ghost int vp_transchar_buf; */
/*@ // illegal_char (optionstr.c): "" when errbuf is NULL, else the formatted E539 message
    // in errbuf->data (opt_error), built with transchar(c). Only "never NULL" and what it may
    // write are used.
    requires errbuf == \null || (\valid_read(errbuf) && \valid(errbuf->data + (0 .. errbuf->size - 1)));
    assigns errbuf->data[0 .. errbuf->size - 1], vp_transchar_buf;
    ensures \result != \null; */
const char *illegal_char(const CharBuf *errbuf, int c);

enum { FSK_KEYCODE = 0x01, FSK_KEEP_X_KEY = 0x02, FSK_SIMPLIFY = 0x08 };
/*@ // find_special_key (keycodes.c): parses a <...> key name at *srcp, reading at most
    // src_len bytes. Only its memory footprint is used here, not its result.
    requires \valid(srcp) && \valid(modp) && \separated(srcp, modp);
    requires \valid_read(*srcp + (0 .. src_len - 1));
    requires did_simplify == \null;
    assigns *srcp, *modp, \result \from *srcp, src_len, flags, (*srcp)[0 .. src_len - 1];
*/
int find_special_key(const char **const srcp, const size_t src_len, int *const modp,
                     const int flags, bool *const did_simplify);
#endif
