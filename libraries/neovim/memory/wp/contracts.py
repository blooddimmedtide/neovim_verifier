"""ACSL contracts for memory.c's string functions, from their doc comments."""

LOGIC = r"""
/*@ // memchr compares bytes as unsigned char; for two chars that is plain equality.
    lemma uchar_eq: \forall char a, b; (unsigned char)a == (unsigned char)b <==> a == b;
*/
/*@ // number of k in [0, n) with s[k] == c
    logic integer count{L}(char *s, char c, integer n) =
      n <= 0 ? 0 : count(s, c, n - 1) + (s[n - 1] == c ? 1 : 0);
*/
/*@ // a string has one length
    lemma str_len_unique{L}: \forall char *s, integer n, m; str_len(s, n) && str_len(s, m) ==> n == m;
*/
/*@ ghost
  // count(s, c, k) is between 0 and k (induction on k, done by the loop)
  /@ requires 0 <= k;
     assigns \nothing;
     ensures 0 <= count(s, c, k) <= k; @/
  void count_le(char *s, char c, size_t k) {
    size_t j = 0;
    /@ loop invariant 0 <= j <= k && 0 <= count(s, c, j) <= j;
       loop assigns j; loop variant k - j; @/
    while (j < k) j++;
  }
*/
/*@ ghost
  // count does not change over a stretch with no c in it
  /@ requires 0 <= a <= b;
     requires \forall integer k; a <= k < b ==> s[k] != c;
     assigns \nothing;
     ensures count(s, c, b) == count(s, c, a); @/
  void count_gap(char *s, char c, size_t a, size_t b) {
    size_t j = a;
    /@ loop invariant a <= j <= b && count(s, c, j) == count(s, c, a);
       loop assigns j; loop variant b - j; @/
    while (j < b) j++;
  }
*/
"""

# Ghost parameters: the length of the string argument, as a specification variable.
GHOST_PARAMS = {
"strcnt": ("size_t strcnt(const char *str, char c)", "size_t n"),
"strchrsub": ("void strchrsub(char *str, char c, char x)", "size_t n"),
"xstpcpy": ("char *xstpcpy(char *restrict dst, const char *restrict src)", "size_t n"),
"xstrlcat": ("size_t xstrlcat(char *const dst, const char *const src, const size_t dsize)", "size_t m, size_t n"),
}

CONTRACTS = {
"xmemcpyz": r"""requires \valid((char *)dst + (0 .. len)) && \valid_read((char *)src + (0 .. len - 1));
    requires \separated((char *)dst + (0 .. len), (char *)src + (0 .. len - 1));
    assigns ((char *)dst)[0 .. len];
    ensures \forall integer i; 0 <= i < len ==> ((char *)dst)[i] == \old(((char *)src)[i]);
    ensures ((char *)dst)[len] == 0;
    ensures \result == dst;""",

"xstrnlen": r"""requires \forall integer i; 0 <= i < n ==>
               (\forall integer j; 0 <= j < i ==> s[j] != 0) ==> \valid_read(s + i);
    assigns \nothing;
    ensures 0 <= \result <= n;
    ensures \forall integer i; 0 <= i < \result ==> s[i] != 0;
    ensures \result < n ==> s[\result] == 0;""",

"xstrchrnul": r"""requires is_str(str);
    assigns \nothing;
    ensures \exists integer i; 0 <= i && \result == str + i && (str[i] == c || str[i] == 0)
            && \forall integer j; 0 <= j < i ==> str[j] != c && str[j] != 0;""",

"xmemscan": r"""requires \forall integer i; 0 <= i < size ==>
               (\forall integer j; 0 <= j < i ==> ((char *)addr)[j] != c) ==> \valid_read((char *)addr + i);
    assigns \nothing;
    ensures \exists integer i; 0 <= i <= size && (char *)\result == (char *)addr + i
            && (i < size ==> ((char *)addr)[i] == c)
            && \forall integer j; 0 <= j < i ==> ((char *)addr)[j] != c;""",

"strchrsub": r"""requires c != 0 && str_len(str, n) && \valid(str + (0 .. n));
    assigns str[0 .. n];
    ensures \forall integer i; 0 <= i <= n ==> str[i] == (\at(str[i], Pre) == c ? x : \at(str[i], Pre));""",

"memchrsub": r"""requires \valid((char *)data + (0 .. len - 1));
    assigns ((char *)data)[0 .. len - 1];
    ensures \forall integer i; 0 <= i < len ==>
              ((char *)data)[i] == (\at(((char *)data)[i], Pre) == c ? x : \at(((char *)data)[i], Pre));""",

"strcnt": r"""requires c != 0 && str_len((char *)str, n);
    assigns \nothing;
    ensures \result == count((char *)str, c, n);""",

"memcnt": r"""requires \valid_read((char *)data + (0 .. len - 1));
    assigns \nothing;
    ensures \result == count((char *)data, c, len);""",

"xstpcpy": r"""requires n < PTRDIFF_MAX;   // no C object is larger
    requires str_len((char *)src, n) && \valid(dst + (0 .. n)) && \separated(dst + (0 .. n), src + (0 .. n));
    assigns dst[0 .. n];
    ensures \result == dst + n && \forall integer i; 0 <= i <= n ==> dst[i] == \at(src[i], Pre);""",

"xstpncpy": r"""requires \valid(dst + (0 .. maxlen - 1));
    requires \forall integer i; 0 <= i < maxlen ==>
               (\forall integer j; 0 <= j < i ==> src[j] != 0) ==> \valid_read(src + i);
    requires \separated(dst + (0 .. maxlen - 1), src + (0 .. maxlen - 1));
    assigns dst[0 .. maxlen - 1];
    ensures \base_addr(\result) == \base_addr(dst) && dst <= \result <= dst + maxlen;
    ensures \forall integer i; 0 <= i < \result - dst ==> \at(src[i], Pre) != 0 && dst[i] == \at(src[i], Pre);
    ensures \result - dst < maxlen ==> \let k = \result - dst; \at(src[k], Pre) == 0;
    ensures \forall integer i; \result - dst <= i < maxlen ==> dst[i] == 0;""",

"xstrlcpy": r"""requires \exists integer n; str_len(src, n);
    requires \valid(dst + (0 .. dsize - 1));
    requires \forall integer n; str_len(src, n) ==> \separated(dst + (0 .. dsize - 1), src + (0 .. n));
    assigns dst[0 .. dsize - 1];
    ensures \forall integer n; \at(str_len(src, n), Pre) ==> \result == n
            && (dsize > 0 ==> (\forall integer i; 0 <= i < \min(n, dsize - 1) ==> dst[i] == \at(src[i], Pre))
                              && dst[\min(n, dsize - 1)] == 0);""",

"xstrlcat": r"""requires dsize > 0 && \valid(dst + (0 .. dsize - 1));
    requires str_len(dst, m) && m < dsize && str_len((char *)src, n);
    requires dsize <= PTRDIFF_MAX && n < PTRDIFF_MAX;   // no C object is larger
    assigns dst[0 .. dsize - 1];
    ensures \result == m + n;
    ensures \forall integer i; 0 <= i < m ==> dst[i] == \at(dst[i], Pre);
    ensures \forall integer i; 0 <= i < \min(n, dsize - m - 1) ==> dst[m + i] == \at(src[i], Pre);
    ensures dst[m + \min(n, dsize - m - 1)] == 0;""",

"xmemrchr": r"""requires \valid_read((uint8_t *)src + (0 .. len - 1));
    assigns \nothing;
    behavior found:
      assumes \exists integer i; 0 <= i < len && ((uint8_t *)src)[i] == c;
      ensures \exists integer i; 0 <= i < len && (uint8_t *)\result == (uint8_t *)src + i
              && ((uint8_t *)src)[i] == c && \forall integer j; i < j < len ==> ((uint8_t *)src)[j] != c;
    behavior not_found:
      assumes \forall integer i; 0 <= i < len ==> ((uint8_t *)src)[i] != c;
      ensures \result == \null;
    complete behaviors; disjoint behaviors;""",

"strequal": r"""requires a == \null || is_str((char *)a);
    requires b == \null || is_str((char *)b);
    assigns \nothing;
    ensures \result <==> (a == \null && b == \null)
            || (a != \null && b != \null && \exists integer n; str_len((char *)a, n) && str_len((char *)b, n)
                && \forall integer i; 0 <= i < n ==> a[i] == b[i]);""",

"strnequal": r"""requires a == \null || b == \null || \forall integer i; 0 <= i < n ==>
               (\forall integer j; 0 <= j < i ==> a[j] != 0 && a[j] == b[j]) ==> \valid_read(a + i) && \valid_read(b + i);
    assigns \nothing;
    ensures \result <==> (a == \null && b == \null)
            || (a != \null && b != \null && \forall integer i; 0 <= i < n ==>
                  (\forall integer j; 0 <= j < i ==> a[j] != 0) ==> a[i] == b[i]);""",
}

LOOPS = {
"xstpcpy": [("  return (char *)memcpy(dst, src, len + 1) + len;", r"""assert len == n;""")],
"xstrlcat": [("  if (slen > dsize - dlen - 1) {", r"""assert dlen == m && slen == n;""")],
"xstpncpy": [("    return dst + srclen;", r"""assert \forall integer i; srclen <= i < maxlen ==> dst[i] == 0;""")],
"strchrsub": [
  ("  while ((str = strchr(str, c))) {", r"""ghost char *s0 = str;"""),
  ("  while ((str = strchr(str, c))) {", r"""ghost char *g = str;"""),
  ("  while ((str = strchr(str, c))) {", r"""loop invariant \base_addr(str) == \base_addr(s0) && s0 <= str <= s0 + n && g == str;
      loop invariant str_len(str, n - (str - s0));
      loop invariant \forall integer k; 0 <= k < str - s0 ==> s0[k] == (\at(str[k], Pre) == c ? x : \at(str[k], Pre));
      loop invariant \forall integer k; str - s0 <= k <= n ==> s0[k] == \at(str[k], Pre);
      loop assigns str, g, s0[0 .. n];
      loop variant n - (str - s0);"""),
  ("    *str++ = x;", r"""assert str - g >= 0 && str - s0 < n;"""),
  ("    *str++ = x;", r"""assert \forall integer j; 0 <= j < str - g ==> g[j] != c;"""),
  ("    *str++ = x;", r"""assert \forall integer k; g - s0 <= k < str - s0 ==> s0[k] == g[k - (g - s0)];"""),
  ("    *str++ = x;", r"""assert \forall integer k; g - s0 <= k < str - s0 ==> s0[k] != c && s0[k] == \at(str[k], Pre);"""),
  ("    *str++ = x;", r"""assert *str == c && s0[str - s0] == c && \let d = str - s0; \at(str[d], Pre) == c;"""),
  ("    *str++ = x;", r"""assert str_len(str + 1, n - (str - s0) - 1);"""),
  ("    *str++ = x;", r"""ghost g = str + 1;"""),
  ("<END>", r"""assert str_len(g, n - (g - s0));"""),
  ("<END>", r"""assert \forall integer j; 0 <= j <= n - (g - s0) ==> g[j] != c;"""),
  ("<END>", r"""assert \forall integer k; g - s0 <= k <= n ==> s0[k] == g[k - (g - s0)];"""),
  ("<END>", r"""assert \forall integer k; g - s0 <= k <= n ==> s0[k] != c && s0[k] == \at(str[k], Pre);"""),
  ("<END>", r"""assert \forall integer k; 0 <= k <= n ==> s0[k] == (\at(str[k], Pre) == c ? x : \at(str[k], Pre));"""),
],
"memchrsub": [
  ("  while ((p = memchr(p, c, (size_t)(end - p)))) {", r"""ghost char *g = p;"""),
  ("  while ((p = memchr(p, c, (size_t)(end - p)))) {", r"""loop invariant \base_addr(p) == \base_addr((char *)data) && (char *)data <= p <= end && g == p;
      loop invariant end == (char *)data + len;
      loop invariant \forall integer k; 0 <= k < p - (char *)data ==>
        ((char *)data)[k] == (\at(((char *)data)[k], Pre) == c ? x : \at(((char *)data)[k], Pre));
      loop invariant \forall integer k; p - (char *)data <= k < len ==> ((char *)data)[k] == \at(((char *)data)[k], Pre);
      loop assigns p, g, ((char *)data)[0 .. len - 1];
      loop variant end - p;"""),
  ("    *p++ = x;", r"""assert p - g >= 0 && p < end;"""),
  ("    *p++ = x;", r"""assert \forall integer j; 0 <= j < p - g ==> g[j] != c;"""),
  ("    *p++ = x;", r"""assert \forall integer k; g - (char *)data <= k < p - (char *)data ==> ((char *)data)[k] == g[k - (g - (char *)data)];"""),
  ("    *p++ = x;", r"""assert \forall integer k; g - (char *)data <= k < p - (char *)data ==> ((char *)data)[k] != c && ((char *)data)[k] == \at(((char *)data)[k], Pre);"""),
  ("    *p++ = x;", r"""assert *p == c && \let d = p - (char *)data; \at(((char *)data)[d], Pre) == c;"""),
  ("    *p++ = x;", r"""ghost g = p + 1;"""),
  ("<END>", r"""assert \forall integer j; 0 <= j < end - g ==> g[j] != c;"""),
  ("<END>", r"""assert \forall integer k; g - (char *)data <= k < len ==> ((char *)data)[k] == g[k - (g - (char *)data)];"""),
  ("<END>", r"""assert \forall integer k; g - (char *)data <= k < len ==> ((char *)data)[k] != c && ((char *)data)[k] == \at(((char *)data)[k], Pre);"""),
],
"strcnt": [
  ("  while ((str = strchr(str, c))) {", r"""ghost char *s0 = (char *)str;"""),
  ("  while ((str = strchr(str, c))) {", r"""ghost char *g = (char *)str;"""),
  ("  while ((str = strchr(str, c))) {", r"""loop invariant \base_addr(str) == \base_addr(s0) && s0 <= str <= s0 + n && g == str;
      loop invariant str_len((char *)str, n - (str - s0));
      loop invariant cnt == count(s0, c, str - s0);
      loop assigns str, cnt, g;
      loop variant n - (str - s0);"""),
  ("    cnt++;", r"""assert str - g >= 0 && str - s0 < n;"""),
  ("    cnt++;", r"""assert \forall integer j; 0 <= j < str - g ==> g[j] != c;"""),
  ("    cnt++;", r"""assert \forall integer k; g - s0 <= k < str - s0 ==> s0[k] == g[k - (g - s0)];"""),
  ("    cnt++;", r"""assert \forall integer k; g - s0 <= k < str - s0 ==> s0[k] != c;"""),
  ("    cnt++;", r"""assert *str == c && s0[str - s0] == c;"""),
  ("    cnt++;", r"""assert str_len((char *)str + 1, n - (str - s0) - 1);"""),
  ("    cnt++;", r"""ghost count_le(s0, c, str - s0);"""),
  ("    cnt++;", r"""ghost count_gap(s0, c, g - s0, str - s0);"""),
  ("    str++;  // Skip the instance of c.", r"""assert cnt == count(s0, c, str - s0 + 1);"""),
  ("    str++;  // Skip the instance of c.", r"""ghost g = (char *)str + 1;"""),
  ("  return cnt;", r"""assert str_len(g, n - (g - s0));"""),
  ("  return cnt;", r"""assert \forall integer j; 0 <= j <= n - (g - s0) ==> g[j] != c;"""),
  ("  return cnt;", r"""assert \forall integer k; g - s0 <= k < n ==> s0[k] == g[k - (g - s0)];"""),
  ("  return cnt;", r"""assert \forall integer k; g - s0 <= k < n ==> s0[k] != c;"""),
  ("  return cnt;", r"""ghost count_gap(s0, c, g - s0, n);"""),
],
"memcnt": [
  ("  while ((ptr = memchr(ptr, c, (size_t)(end - ptr))) != NULL) {", r"""ghost char *g = (char *)ptr;"""),
  ("  while ((ptr = memchr(ptr, c, (size_t)(end - ptr))) != NULL) {", r"""loop invariant \base_addr(ptr) == \base_addr((char *)data) && (char *)data <= ptr <= end && g == ptr;
      loop invariant end == (char *)data + len;
      loop invariant \valid_read(ptr + (0 .. end - ptr - 1));
      loop invariant cnt == count((char *)data, c, ptr - (char *)data);
      loop assigns ptr, cnt, g;
      loop variant end - ptr;"""),
  ("    cnt++;", r"""assert ptr - g >= 0 && ptr < end;"""),
  ("    cnt++;", r"""assert \forall integer j; 0 <= j < ptr - g ==> g[j] != c;"""),
  ("    cnt++;", r"""assert \forall integer k; g - (char *)data <= k < ptr - (char *)data ==> ((char *)data)[k] == g[k - (g - (char *)data)];"""),
  ("    cnt++;", r"""assert \forall integer k; g - (char *)data <= k < ptr - (char *)data ==> ((char *)data)[k] != c;"""),
  ("    cnt++;", r"""assert *ptr == c && ((char *)data)[ptr - (char *)data] == c;"""),
  ("    cnt++;", r"""ghost count_le((char *)data, c, ptr - (char *)data);"""),
  ("    cnt++;", r"""ghost count_gap((char *)data, c, g - (char *)data, ptr - (char *)data);"""),
  ("    ptr++;  // Skip the instance of c.", r"""assert cnt == count((char *)data, c, ptr - (char *)data + 1);"""),
  ("    ptr++;  // Skip the instance of c.", r"""ghost g = (char *)ptr + 1;"""),
  ("  return cnt;", r"""assert \forall integer j; 0 <= j < end - g ==> g[j] != c;"""),
  ("  return cnt;", r"""assert \forall integer k; g - (char *)data <= k < len ==> ((char *)data)[k] == g[k - (g - (char *)data)];"""),
  ("  return cnt;", r"""assert \forall integer k; g - (char *)data <= k < len ==> ((char *)data)[k] != c;"""),
  ("  return cnt;", r"""ghost count_gap((char *)data, c, g - (char *)data, len);"""),
],
"xmemrchr": [("  while (len--) {", r"""loop invariant 0 <= len <= \at(len, Pre);
      loop invariant \forall integer j; len <= j < \at(len, Pre) ==> ((uint8_t *)src)[j] != c;
      loop assigns len;
      loop variant len;""")],
}
