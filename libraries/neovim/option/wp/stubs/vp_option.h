// Contracts for what the option-value helpers call outside themselves. Trusted
// (listed in ../CLAIM.md); no axioms.
#ifndef VP_OPTION_H
#define VP_OPTION_H
#include <stddef.h>
#include <stdint.h>
#include "vp_string.h"

/*@ // vim_strchr (strings.c) for an ASCII c (the only kind these helpers pass):
    // for 0 < c < 0x80 its body is `return (char *)strchr(string, c);`, so this is
    // the C11 strchr contract from vp_string.h restricted to non-NUL c.
    requires 0 < c < 0x80;
    requires is_str((char *)string);
    assigns \result \from string, c, ((char *)string)[0 ..];
    behavior found:
      assumes \exists integer n, i; str_len((char *)string, n) && 0 <= i < n && string[i] == (char)c;
      ensures \exists integer i; 0 <= i && \result == string + i && string[i] == (char)c
              && \forall integer j; 0 <= j < i ==> string[j] != (char)c && string[j] != 0;
    behavior not_found:
      assumes \forall integer n, i; str_len((char *)string, n) && 0 <= i < n ==> string[i] != (char)c;
      ensures \result == \null;
    complete behaviors; disjoint behaviors; */
char *vim_strchr(const char *const string, const int c);
#endif
