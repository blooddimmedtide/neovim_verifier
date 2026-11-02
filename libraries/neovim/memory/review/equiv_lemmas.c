#include "vp_string.h"
/*@ lemma decomp: \forall char *s, *q; \base_addr(q) == \base_addr(s) ==> q == s + (q - s);
    lemma str_ptr_to_idx{L}: \forall char *s, integer n; str_len(s, n) ==>
      (0 <= n && \valid_read(s + (0 .. n)) && s[n] == 0 && \forall integer i; 0 <= i < n ==> s[i] != 0);
    lemma str_idx_to_ptr{L}: \forall char *s, integer n;
      (0 <= n && \valid_read(s + (0 .. n)) && s[n] == 0 && \forall integer i; 0 <= i < n ==> s[i] != 0) ==> str_len(s, n);
    lemma set_ptr_to_idx{L}: \forall char *d, integer n, char c;
      (\forall char *q; \base_addr(q) == \base_addr(d) && d <= q < d + n ==> *q == c) ==> \forall integer i; 0 <= i < n ==> d[i] == c;
    lemma set_idx_to_ptr{L}: \forall char *d, integer n, char c;
      (\forall integer i; 0 <= i < n ==> d[i] == c) ==> \forall char *q; \base_addr(q) == \base_addr(d) && d <= q < d + n ==> *q == c;
*/
