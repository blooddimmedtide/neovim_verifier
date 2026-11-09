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

/*@ // illegal_char (optionstr.c): "" when errbuf is NULL, else the formatted E539 message
    // in errbuf->data (opt_error). Only "never NULL" and what it may write are used.
    requires errbuf == \null || (\valid_read(errbuf) && \valid(errbuf->data + (0 .. errbuf->size - 1)));
    assigns errbuf->data[0 .. errbuf->size - 1];
    ensures \result != \null; */
const char *illegal_char(const CharBuf *errbuf, int c);
#endif
