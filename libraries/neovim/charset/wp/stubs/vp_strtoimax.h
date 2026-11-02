// Contract for strtoimax with base 10 (C11 7.8.2.3 and 7.22.1.4, "C" locale), the only
// way charset.c calls it. No axioms. The C library (glibc) is trusted to meet it.
// errno is modeled as a plain global int (vp_errno); ERANGE is 34 on Linux.
#ifndef VP_STRTOIMAX_H
#define VP_STRTOIMAX_H
#include <stdint.h>
extern int vp_errno;   // errno (glibc: *__errno_location()), a plain global here
#define errno vp_errno
#define ERANGE 34

/*@ // isspace in the "C" locale: space, \t \n \v \f \r
    predicate c_space(integer c) = c == 32 || (9 <= c <= 13);
    // decimal value of s[a .. b-1] (digits)
    logic integer decv{L}(char *s, integer a, integer b) =
      b <= a ? 0 : 10 * decv(s, a, b - 1) + (s[b - 1] - 48);
    // the subject sequence: w leading spaces, an optional sign, digits s[d .. e-1]
    predicate subj{L}(char *s, integer w, integer e) =
      0 <= w && (\forall integer k; 0 <= k < w ==> c_space(s[k])) && !c_space(s[w])
      && \let d = w + ((s[w] == 43 || s[w] == 45) ? 1 : 0);
         d <= e && (\forall integer k; d <= k < e ==> 48 <= s[k] <= 57) && !(48 <= s[e] <= 57);
    logic integer sdigits{L}(char *s, integer w) = w + ((s[w] == 43 || s[w] == 45) ? 1 : 0);
    logic integer svalue{L}(char *s, integer w, integer e) =
      s[w] == 45 ? -decv(s, sdigits(s, w), e) : decv(s, sdigits(s, w), e);
*/

/*@ requires base == 10 && str_len((char *)nptr, n);
    requires \valid(endptr) && \separated(endptr, nptr + (0 .. n), &errno);
    assigns \result, *endptr, errno;
    ensures \forall integer w, e; \at(subj((char *)nptr, w, e), Pre) ==>
      (e == \at(sdigits((char *)nptr, w), Pre) ==> \result == 0 && *endptr == nptr && errno == \old(errno))
      && (e > \at(sdigits((char *)nptr, w), Pre) ==> *endptr == nptr + e
          && \let v = \at(svalue((char *)nptr, w, e), Pre);
             (v > INTMAX_MAX ==> \result == INTMAX_MAX && errno == ERANGE)
             && (v < INTMAX_MIN ==> \result == INTMAX_MIN && errno == ERANGE)
             && (INTMAX_MIN <= v <= INTMAX_MAX ==> \result == v && errno == \old(errno)));
*/
intmax_t strtoimax(const char *nptr, char **endptr, int base) /*@ ghost (size_t n) */;
#endif
