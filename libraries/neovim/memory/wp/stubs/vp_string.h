// Contracts for the C library string functions memory.c calls, written from
// the C standard (C11 7.24), with no axioms. They replace Frama-C's libc
// string.h, whose axiomatic memchr compares a signed char with an int (wrong
// for c > 127).
// The C library itself (glibc) is trusted to meet them.
#ifndef VP_STRING_H
#define VP_STRING_H
#include <stddef.h>

/*@ // s holds a string of length n: n readable non-NUL bytes, then a NUL.
    // (The non-NUL part quantifies over pointers, not indices: WP's memory model
    // puts offset arithmetic inside index triggers, so provers miss instances
    // such as i := j + 1; a pointer variable matches any access.)
    predicate str_len{L}(char *s, integer n) =
      0 <= n && \valid_read(s + (0 .. n)) && s[n] == 0
      && \forall char *q; \base_addr(q) == \base_addr(s) && s <= q < s + n ==> *q != 0;
    predicate is_str{L}(char *s) = \exists integer n; str_len(s, n);
    // byte i of s matches c as memchr compares: both as unsigned char
    predicate byte_is{L}(char *s, integer i, int c) = (unsigned char)s[i] == (unsigned char)c;
*/

/*@ requires is_str((char *)s);
    assigns \result \from ((char *)s)[0 ..];
    ensures str_len((char *)s, \result); */
size_t strlen(const char *s);

/*@ // reads bytes in order and stops at the first match (C11 7.24.5.1)
    requires \forall integer i; 0 <= i < n ==>
               (\forall integer j; 0 <= j < i ==> !byte_is((char *)s, j, c)) ==> \valid_read((char *)s + i);
    assigns \result \from s, c, n, ((char *)s)[0 .. n - 1];
    behavior found:
      assumes \exists integer i; 0 <= i < n && byte_is((char *)s, i, c);
      ensures \exists integer i; 0 <= i < n && (char *)\result == (char *)s + i && byte_is((char *)s, i, c)
              && \forall integer j; 0 <= j < i ==> !byte_is((char *)s, j, c);
    behavior not_found:
      assumes \forall integer i; 0 <= i < n ==> !byte_is((char *)s, i, c);
      ensures \result == \null;
    complete behaviors; disjoint behaviors; */
void *memchr(const void *s, int c, size_t n);

/*@ requires is_str((char *)s);
    assigns \result \from s, c, ((char *)s)[0 ..];
    behavior found:
      assumes \exists integer n, i; str_len((char *)s, n) && 0 <= i <= n && s[i] == (char)c;
      ensures \exists integer i; 0 <= i && \result == s + i && s[i] == (char)c
              && \forall integer j; 0 <= j < i ==> s[j] != (char)c && s[j] != 0;
    behavior not_found:
      assumes \forall integer n, i; str_len((char *)s, n) && 0 <= i <= n ==> s[i] != (char)c;
      ensures \result == \null;
    complete behaviors; disjoint behaviors; */
char *strchr(const char *s, int c);

/*@ requires \valid((char *)d + (0 .. n - 1)) && \valid_read((char *)s + (0 .. n - 1));
    requires \separated((char *)d + (0 .. n - 1), (char *)s + (0 .. n - 1));
    assigns ((char *)d)[0 .. n - 1] \from ((char *)s)[0 .. n - 1];
    ensures \forall integer i; 0 <= i < n ==> ((char *)d)[i] == \old(((char *)s)[i]);
    ensures \result == d; */
void *memcpy(void *restrict d, const void *restrict s, size_t n);

/*@ requires \valid((char *)d + (0 .. n - 1)) && \valid_read((char *)s + (0 .. n - 1));
    assigns ((char *)d)[0 .. n - 1] \from ((char *)s)[0 .. n - 1];
    ensures \forall integer i; 0 <= i < n ==> ((char *)d)[i] == \old(((char *)s)[i]);
    ensures \result == d; */
void *memmove(void *d, const void *s, size_t n);

/*@ requires \valid((char *)d + (0 .. n - 1));
    assigns ((char *)d)[0 .. n - 1] \from c;
    ensures \forall char *q; \base_addr(q) == \base_addr((char *)d) && (char *)d <= q < (char *)d + n ==> *q == (char)c;
    ensures \result == d; */
void *memset(void *d, int c, size_t n);

/*@ requires is_str((char *)a) && is_str((char *)b);
    assigns \result \from ((char *)a)[0 ..], ((char *)b)[0 ..];
    ensures \result == 0 <==> \exists integer n; str_len((char *)a, n) && str_len((char *)b, n)
                              && \forall integer i; 0 <= i < n ==> a[i] == b[i]; */
int strcmp(const char *a, const char *b);

/*@ // compares at most n bytes, stopping after a NUL in both
    requires \forall integer i; 0 <= i < n ==>
               (\forall integer j; 0 <= j < i ==> a[j] != 0 && a[j] == b[j]) ==> \valid_read(a + i) && \valid_read(b + i);
    assigns \result \from ((char *)a)[0 .. n - 1], ((char *)b)[0 .. n - 1];
    ensures \result == 0 <==> \forall integer i; 0 <= i < n ==>
                                (\forall integer j; 0 <= j < i ==> a[j] != 0) ==> a[i] == b[i]; */
int strncmp(const char *a, const char *b, size_t n);
#endif
