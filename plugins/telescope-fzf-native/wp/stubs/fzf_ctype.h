// <ctype.h> for the WP proof of fzf.c: isspace and tolower as the C standard
// defines them in the "C" locale (C11 7.4.1.10, 7.4.2.1). glibc behaves so in
// the "C" locale and in every UTF-8 locale (difftest/libc_check.c checks the C
// locale on all inputs). No axioms.
#ifndef FZF_CTYPE_H
#define FZF_CTYPE_H
/*@ requires 0 <= c <= 255 || c == -1;
    assigns \result \from c;
    ensures (\result != 0) <==> (c == ' ' || (9 <= c <= 13)); */
int isspace(int c);
/*@ requires 0 <= c <= 255 || c == -1;
    assigns \result \from c;
    ensures 'A' <= c <= 'Z' ==> \result == c - 'A' + 'a';
    ensures !('A' <= c <= 'Z') ==> \result == c; */
int tolower(int c);
#endif
