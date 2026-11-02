#include "vp_string.h"
/*@ requires \forall integer i; 0 <= i < n ==> d[i] == c;
    requires \base_addr(q) == \base_addr(d) && d <= q < d + n;
    assigns \nothing;
    ensures *q == c; */
void set_pt(char *d, char *q, long n, char c) {
  /*@ assert r: 0 <= q - d < n; */
  /*@ assert e: q == d + (q - d); */
  /*@ assert v: d[q - d] == c; */
  /*@ assert w: *(d + (q - d)) == c; */
}
/*@ requires \forall integer i; 0 <= i < n ==> s[i] != 0;
    requires \base_addr(q) == \base_addr(s) && s <= q < s + n;
    assigns \nothing;
    ensures *q != 0; */
void str_pt(char *s, char *q, long n) {
  /*@ assert r: 0 <= q - s < n; */
  /*@ assert e: q == s + (q - s); */
  /*@ assert v: s[q - s] != 0; */
  /*@ assert w: *(s + (q - s)) != 0; */
}
