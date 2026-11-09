"""ACSL contracts for strings.c's string helpers, written from their comments.

Character classes use ASCII codes: 'a'..'z' 97..122, 'A'..'Z' 65..90, space 32, TAB 9,
backslash 92, Ctrl-V 22.
"""
S = "src/nvim/strings.c"
A = "src/nvim/ascii_defs.h"
PIECES = [
    (A, "ascii_iswhite", "3cbe82f79096229a84ed15445d03821a9ac36721a7b0f146bcc2e18c8566b0cf"),
    (S, "xstrnsave", "516350a67b2f614eb11958bda5e49292dc62ba376f5236ddbe7b312ceed98f62"),
    (S, "vim_strup", "385c2ce76d346eeb0234bcb35d5ad05240b12269691dc87385b0939d75d1ce8d"),
    (S, "vim_strcpy_up", "c257bdc70bfd9a0b5865d0a1632d0fb35db67c6c151111c1e95c8ca66ac1de85"),
    (S, "vim_strncpy_up", "4a92f36dc9a8e0cc179c8d3e14d6656ceae3ceac588b546bdb65916b4b600f81"),
    (S, "vim_memcpy_up", "b5709948fa8bf927231f0ced0e4a2f1cb2d3d2eafa99917fae6bf5c43aef8735"),
    (S, "vim_strsave_up", "2345393f7e8041db2c86fe4e78fa775d6e3a5a71140d2333e65f37e5fe4fb5ab"),
    (S, "vim_strnsave_up", "4ab62646db65448fc9344a36f6b46c2163c6b2440dfc94da31b6341b49abb672"),
    (S, "del_trailing_spaces", "3fba0f385974c64161d6cd0d67412058b8a3e8061291f281d21c1cad2780e871"),
    (S, "vim_strnicmp_asc", "2eea2aad5190c0448d77fbec55c0521a541ddd083186d13de8af54f465c5f87a"),
    (S, "has_non_ascii", "3850744fa7e78e4c366eba0d4ccf10a81144834ebbcaa6e11d6312dbd8d31bf1"),
    (S, "has_non_ascii_len", "2f2f750c552003aead0760beb941e9e1e14583fd9530939e049d5afe0c04408b"),
    (S, "concat_str", "05da8a796cd08f483f0f5e92b01c8406136da738964107af21b1d8c827c56f2c"),
]
FIXED_SHA = {}
PRELUDE_EXTRA = r"""#include "vp_string_more.h"
#define FUNC_ATTR_MALLOC
#define TOLOWER_ASC(c) (((c) < 'A' || (c) > 'Z') ? (c) : (c) + ('a' - 'A'))
#define STRCPY(d, s)        strcpy((char *)(d), (char *)(s))  // NOLINT(runtime/printf)
"""
PRELUDE_CHECKS = [
    ("src/nvim/macros_defs.h", "#define TOLOWER_ASC(c) (((c) < 'A' || (c) > 'Z') ? (c) : (c) + ('a' - 'A'))"),
    ("src/nvim/memory.h", "#define STRCPY(d, s)        strcpy((char *)(d), (char *)(s))  // NOLINT(runtime/printf)"),
]

LOGIC = r"""
/*@ predicate is_white(integer c) = c == 32 || c == 9;
    // ASCII upper case of a byte; other bytes unchanged
    logic integer up(integer c) = 97 <= c <= 122 ? c - 32 : c;
    // ASCII lower case of a char value (TOLOWER_ASC on char)
    logic integer low(integer c) = 65 <= c <= 90 ? c + 32 : c;
    predicate is_esc(integer c) = c == 92 || c == 22;
    // xstrnsave / vim_strnsave_up: s has k readable non-NUL bytes, then a NUL or the limit len
    predicate prefix_len{L}(char *s, integer k, integer len) =
      0 <= k <= len && \valid_read(s + (0 .. k - 1)) && (\forall integer i; 0 <= i < k ==> s[i] != 0)
      && (k < len ==> \valid_read(s + k) && s[k] == 0);
*/
"""

GHOST_PARAMS = {
    "xstrnsave": ("char *xstrnsave(const char *string, size_t len)", "size_t k"),
    "vim_strup": ("void vim_strup(char *p)", "size_t n"),
    "vim_strcpy_up": ("void vim_strcpy_up(char *restrict dst, const char *restrict src)", "size_t n"),
    "vim_strsave_up": ("char *vim_strsave_up(const char *string)", "size_t n"),
    "vim_strnsave_up": ("char *vim_strnsave_up(const char *string, size_t len)", "size_t k"),
    "del_trailing_spaces": ("void del_trailing_spaces(char *ptr)", "size_t n"),
    "has_non_ascii": ("bool has_non_ascii(const char *s)", "size_t n"),
    "concat_str": ("char *concat_str(const char *restrict str1, const char *restrict str2)", "size_t n1, size_t n2"),
}
GHOST_ARGS = {
    "xstrnsave": [("xmallocz(len)", "(char *)string, k, (char *)string, k")],
    "vim_strsave_up": [("xmalloc(strlen(string) + 1)", "(char *)string, n + 1, (char *)string, n + 1"),
                       ("vim_strcpy_up(p1, string)", "n")],
    "vim_strnsave_up": [("xmalloc(len + 1)", "(char *)string, k, (char *)string, k")],
    "concat_str": [("xmalloc(l + strlen(str2) + 1)", "(char *)str1, n1 + 1, (char *)str2, n2 + 1")],
}

_ALLOC = r"""requires vp_live < 2147483647;
    ensures vp_live == \old(vp_live) + 1 && vp_last == \result;"""
CONTRACTS = {
    "ascii_iswhite": r"""assigns \nothing; ensures \result != 0 <==> is_white(c);""",
    # "Copy up to len bytes ... terminate with a NUL. The allocated memory always has size
    # len + 1, even when string is shorter." (strncpy semantics: the rest is NUL)
    "xstrnsave": rf"""requires prefix_len((char *)string, k, len) && len < 18446744073709551615;
    {_ALLOC}
    ensures \valid(\result + (0 .. len)) && \result[len] == 0;
    ensures \forall integer i; 0 <= i < len ==> \result[i] == (i < k ? \at(string[i], Pre) : 0);""",
    "vim_strup": r"""requires str_len(p, n) && \valid(p + (0 .. n));
    assigns p[0 .. n];
    ensures \forall integer i; 0 <= i <= n ==> p[i] == up(\at(p[i], Pre));""",
    "vim_strcpy_up": r"""requires str_len((char *)src, n) && \valid(dst + (0 .. n)) && \separated(dst + (0 .. n), src + (0 .. n));
    assigns dst[0 .. n];
    ensures \forall integer i; 0 <= i <= n ==> dst[i] == up(\at(src[i], Pre));""",
    # strncpy-like: copies (upper-cased) up to the NUL or n bytes, then one NUL
    "vim_strncpy_up": r"""requires \valid(dst + (0 .. n));
    requires \forall char *r; \base_addr(r) == \base_addr(src) && src <= r < src + n ==>
               (\forall char *q; \base_addr(q) == \base_addr(src) && src <= q < r ==> *q != 0) ==> \valid_read(r);
    requires \separated(dst + (0 .. n), src + (0 .. n - 1));
    assigns dst[0 .. n];
    ensures \forall integer k; 0 <= k <= n && (\forall integer j; 0 <= j < k ==> \at(src[j], Pre) != 0)
              && (k < n ==> \at(src[k], Pre) == 0) ==>
              dst[k] == 0 && \forall integer i; 0 <= i < k ==> dst[i] == up(\at(src[i], Pre));""",
    "vim_memcpy_up": r"""requires \valid(dst + (0 .. n - 1)) && \valid_read(src + (0 .. n - 1));
    requires \separated(dst + (0 .. n - 1), src + (0 .. n - 1));
    assigns dst[0 .. n - 1];
    ensures \forall integer i; 0 <= i < n ==> dst[i] == up(\at(src[i], Pre));""",
    "vim_strsave_up": rf"""requires str_len((char *)string, n) && n < 9223372036854775807;
    {_ALLOC}
    ensures \valid(\result + (0 .. n)) && \forall integer i; 0 <= i <= n ==> \result[i] == up(\at(string[i], Pre));""",
    "vim_strnsave_up": rf"""requires prefix_len((char *)string, k, len) && len < 18446744073709551615;
    {_ALLOC}
    ensures \valid(\result + (0 .. len)) && \result[k] == 0;
    ensures \forall integer i; 0 <= i < k ==> \result[i] == up(\at(string[i], Pre));""",
    # "delete spaces at the end of a string": trailing spaces/TABs become NUL, except one
    # escaped by a backslash or Ctrl-V before it; the first byte is never removed.
    # n == 0: the code forms ptr - 1 (only compared), so ptr must not be the start of its
    # object (true at the only call, ex_docmd.c: eap->arg points into the command line).
    "del_trailing_spaces": r"""requires str_len(ptr, n) && \valid(ptr + (0 .. n));
    requires n == 0 ==> \offset(ptr) >= 1;
    assigns ptr[1 .. n];
    ensures \exists integer t; (n == 0 ? t == 0 : 1 <= t <= n)
      && (\forall integer q; t <= q < n ==> is_white(\at(ptr[q], Pre)) && !is_esc(\at(ptr[q - 1], Pre)))
      && (\let k = t; k >= 2 ==> !(is_white(\at(ptr[k - 1], Pre)) && !is_esc(\at(ptr[k - 2], Pre))))
      && (\forall integer i; 0 <= i < t ==> ptr[i] == \at(ptr[i], Pre))
      && (\forall integer i; t <= i < n ==> ptr[i] == 0)
      && ptr[n] == 0;""",
    "vim_strnicmp_asc": r"""requires \forall integer i; 0 <= i < len ==>
               (\forall integer j; 0 <= j < i ==> low(s1[j]) == low(s2[j]) && s1[j] != 0)
               ==> \valid_read(s1 + i) && \valid_read(s2 + i);
    // the same, with the index as a pointer offset (what the provers match on)
    requires \forall char *r; \base_addr(r) == \base_addr(s1) && s1 <= r < s1 + len ==>
               (\forall integer j; 0 <= j < r - s1 ==> low(s1[j]) == low(s2[j]) && s1[j] != 0)
               ==> \valid_read(r) && \valid_read(s2 + (r - s1));
    assigns \nothing;
    ensures \forall integer k; 0 <= k <= len
              && (\forall integer j; 0 <= j < k ==> low(s1[j]) == low(s2[j]) && s1[j] != 0)
              && (k == len || low(s1[k]) != low(s2[k]) || s1[k] == 0) ==>
              \result == (k < len ? low(s1[k]) - low(s2[k]) : 0);""",
    "has_non_ascii": r"""requires s != \null ==> str_len((char *)s, n);
    assigns \nothing;
    ensures \result != 0 <==> s != \null && \exists char *r; \base_addr(r) == \base_addr(s) && s <= r < s + n && (unsigned char)*r >= 128;""",
    "has_non_ascii_len": r"""requires s != \null ==> \valid_read(s + (0 .. len - 1));
    assigns \nothing;
    ensures \result != 0 <==> s != \null && \exists integer i; 0 <= i < len && (unsigned char)s[i] >= 128;""",
    "concat_str": rf"""requires str_len((char *)str1, n1) && str_len((char *)str2, n2);
    requires n1 < 9223372036854775807 && n2 < 9223372036854775807;   // no object is larger
    {_ALLOC}
    ensures \valid(\result + (0 .. n1 + n2));
    ensures \forall integer i; 0 <= i < n1 ==> \result[i] == \at(str1[i], Pre);
    ensures \forall integer i; 0 <= i <= n2 ==> \result[n1 + i] == \at(str2[i], Pre);""",
}

_SP = r"""loop invariant \base_addr({v}) == \base_addr({x}) && {x} <= {v} <= {x} + n;"""
LOOPS = {
    "vim_strup": [("  while ((c = (uint8_t)(*p)) != NUL) {",
        r"""loop invariant \base_addr(p) == \base_addr(\at(p, Pre)) && \at(p, Pre) <= p <= \at(p, Pre) + n;
      loop invariant \forall integer i; 0 <= i < p - \at(p, Pre) ==> \at(p, Pre)[i] == up(\at(\at(p, Pre)[i], Pre));
      loop invariant \forall integer i; p - \at(p, Pre) <= i <= n ==> \at(p, Pre)[i] == \at(\at(p, Pre)[i], Pre);
      loop assigns p, c, \at(p, Pre)[0 .. n - 1];
      loop variant n - (p - \at(p, Pre));""")],
    "vim_strcpy_up": [("  while ((c = (uint8_t)(*src++)) != NUL) {",
        r"""loop invariant \base_addr(src) == \base_addr(\at(src, Pre)) && \at(src, Pre) <= src <= \at(src, Pre) + n;
      loop invariant dst - \at(dst, Pre) == src - \at(src, Pre) && \base_addr(dst) == \base_addr(\at(dst, Pre));
      loop invariant \forall integer i; 0 <= i < src - \at(src, Pre) ==> \at(dst, Pre)[i] == up(\at(\at(src, Pre)[i], Pre));
      loop assigns src, dst, c, \at(dst, Pre)[0 .. n - 1];
      loop variant n - (src - \at(src, Pre));""")],
    "vim_strncpy_up": [("  while (n-- && (c = (uint8_t)(*src++)) != NUL) {",
        r"""loop invariant \base_addr(src) == \base_addr(\at(src, Pre)) && \at(src, Pre) <= src;
      loop invariant 0 <= n <= \at(n, Pre) && src - \at(src, Pre) == \at(n, Pre) - n;
      loop invariant dst - \at(dst, Pre) == src - \at(src, Pre) && \base_addr(dst) == \base_addr(\at(dst, Pre));
      loop invariant \forall char *q; \base_addr(q) == \base_addr(src) && \at(src, Pre) <= q < src ==> \at(*q, Pre) != 0;
      loop invariant \forall integer i; 0 <= i < src - \at(src, Pre) ==> \at(dst, Pre)[i] == up(\at(\at(src, Pre)[i], Pre));
      loop assigns src, dst, c, n, \at(dst, Pre)[0 .. \at(n, Pre) - 1];
      loop variant n;"""),
        ("  *dst = NUL;", r"""assert \let k = dst - \at(dst, Pre); 0 <= k <= \at(n, Pre)
        && (\forall integer j; 0 <= j < k ==> \at(src, Pre)[j] != 0) && (k < \at(n, Pre) ==> \at(src, Pre)[k] == 0)
        && \forall integer i; 0 <= i < k ==> \at(dst, Pre)[i] == up(\at(\at(src, Pre)[i], Pre));""")],
    "vim_memcpy_up": [("  while (n--) {",
        r"""loop invariant 0 <= n <= \at(n, Pre) && src - \at(src, Pre) == \at(n, Pre) - n;
      loop invariant dst - \at(dst, Pre) == src - \at(src, Pre);
      loop invariant \base_addr(src) == \base_addr(\at(src, Pre)) && \base_addr(dst) == \base_addr(\at(dst, Pre));
      loop invariant \forall integer i; 0 <= i < src - \at(src, Pre) ==> \at(dst, Pre)[i] == up(\at(\at(src, Pre)[i], Pre));
      loop assigns src, dst, c, n, \at(dst, Pre)[0 .. \at(n, Pre) - 1];
      loop variant n;""")],
    "del_trailing_spaces": [("  while (--q > ptr && ascii_iswhite(q[0]) && q[-1] != '\\\\' && q[-1] != Ctrl_V) {", "ghost size_t t = n;"),
        ("    *q = NUL;", "ghost t = (size_t)(q - ptr);"),
        ("    *q = NUL;\n  }\n", r"""assert t == (n == 0 ? 0 : q + 1 - ptr) && (n == 0 ? t == 0 : 1 <= t <= n)
    && (\forall integer i; t <= i < n ==> ptr[i] == 0 && is_white(\at(ptr[i], Pre)) && !is_esc(\at(ptr[i - 1], Pre)))
    && (\let k = t; k >= 2 ==> !(is_white(\at(ptr[k - 1], Pre)) && !is_esc(\at(ptr[k - 2], Pre))))
    && (\forall integer i; 0 <= i < t ==> ptr[i] == \at(ptr[i], Pre)) && ptr[n] == 0;""", None, "after"),
        ("  while (--q > ptr && ascii_iswhite(q[0]) && q[-1] != '\\\\' && q[-1] != Ctrl_V) {",
        r"""loop invariant \base_addr(q) == \base_addr(ptr) && ptr <= q <= ptr + n;
      loop invariant n > 0 ==> ptr < q;
      loop invariant \forall integer i; q - ptr <= i < n ==> is_white(\at(ptr[i], Pre)) && !is_esc(\at(ptr[i - 1], Pre)) && i >= 1;
      loop invariant \forall integer i; 0 <= i < q - ptr ==> ptr[i] == \at(ptr[i], Pre);
      loop invariant \forall integer i; q - ptr <= i < n ==> ptr[i] == 0;
      loop invariant t == q - ptr;
      loop assigns q, t, ptr[1 .. n - 1];
      loop variant q - ptr;""")],
    "vim_strnicmp_asc": [("  while (len > 0) {",
        r"""loop invariant 0 <= len <= \at(len, Pre) && s1 - \at(s1, Pre) == \at(len, Pre) - len && s2 - \at(s2, Pre) == s1 - \at(s1, Pre);
      loop invariant \base_addr(s1) == \base_addr(\at(s1, Pre)) && \base_addr(s2) == \base_addr(\at(s2, Pre));
      loop invariant \forall integer j; 0 <= j < s1 - \at(s1, Pre) ==> low(\at(s1, Pre)[j]) == low(\at(s2, Pre)[j]) && \at(s1, Pre)[j] != 0;
      loop invariant i == 0;
      loop assigns s1, s2, len, i;
      loop variant len;""")],
    "has_non_ascii": [("    for (const char *p = s; *p != NUL; p++) {",
        r"""loop invariant \base_addr(p) == \base_addr(s) && s <= p <= s + n;
      loop invariant \forall integer i; 0 <= i < p - s ==> (unsigned char)s[i] < 128;
      loop invariant \forall char *r; \base_addr(r) == \base_addr(s) && s <= r < p ==> (unsigned char)*r < 128;
      loop assigns p;
      loop variant n - (p - s);""")],
    "has_non_ascii_len": [("    for (size_t i = 0; i < len; i++) {",
        r"""loop invariant 0 <= i <= len && \forall integer j; 0 <= j < i ==> (unsigned char)s[j] < 128;
      loop assigns i;
      loop variant len - i;""")],
}
