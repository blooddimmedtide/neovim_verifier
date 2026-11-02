// Contracts for strncpy, strcpy and strstr (C11 7.24.2.4, 7.24.2.3, 7.24.5.7), no axioms.
// The C library (glibc) is trusted to meet them.
#ifndef VP_STRING_MORE_H
#define VP_STRING_MORE_H
#include "vp_string.h"

/*@ // needle[0 .. m-1] occurs in h at i
    predicate occ{L}(char *h, integer i, char *nd, integer m) = \forall integer k; 0 <= k < m ==> h[i + k] == nd[k];
*/

/*@ // copies s up to its NUL or n bytes, then pads d[.. n-1] with NUL
    requires \valid(d + (0 .. n - 1));
    requires \forall integer i; 0 <= i < n ==>
               (\forall integer j; 0 <= j < i ==> s[j] != 0) ==> \valid_read(s + i);
    requires \separated(d + (0 .. n - 1), s + (0 .. n - 1));
    assigns d[0 .. n - 1];
    ensures \result == d;
    ensures \forall integer i; 0 <= i < n ==>
              d[i] == ((\forall integer j; 0 <= j <= i ==> \at(s[j], Pre) != 0) ? \at(s[i], Pre) : 0); */
char *strncpy(char *restrict d, const char *restrict s, size_t n);

/*@ requires is_str((char *)s);
    requires \forall integer m; str_len((char *)s, m) ==> \valid(d + (0 .. m)) && \separated(d + (0 .. m), s + (0 .. m));
    assigns d[0 ..];   // d's object from d on; the exact bytes are in the ensures
    ensures \result == d;
    ensures \forall integer m; \at(str_len((char *)s, m), Pre) ==> \forall integer i; 0 <= i <= m ==> d[i] == \at(s[i], Pre); */
char *strcpy(char *restrict d, const char *restrict s);

/*@ // first occurrence of the needle (length m) in the haystack (length hn); h for m == 0
    requires is_str((char *)h) && is_str((char *)nd);
    assigns \result \from h, ((char *)h)[0 ..], ((char *)nd)[0 ..];
    ensures \forall integer hn, m; str_len((char *)h, hn) && str_len((char *)nd, m) ==>
      ((\exists integer i; 0 <= i && i + m <= hn && occ((char *)h, i, (char *)nd, m)) ==>
         \exists integer i; 0 <= i && i + m <= hn && \result == h + i && occ((char *)h, i, (char *)nd, m)
           && \forall integer j; 0 <= j < i ==> !occ((char *)h, j, (char *)nd, m))
      && ((\forall integer i; 0 <= i && i + m <= hn ==> !occ((char *)h, i, (char *)nd, m)) ==> \result == \null); */
char *strstr(const char *h, const char *nd);
#endif
