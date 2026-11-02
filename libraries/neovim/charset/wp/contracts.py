"""ACSL contracts for charset.c's string helpers, written from their doc comments.

Character classes and values are spelled with ASCII codes, not with the code's
own helpers: ' ' 32, TAB 9, LF 10, CR 13, '0'..'9' 48..57, 'A'..'F' 65..70,
'a'..'f' 97..102, backslash 92, Ctrl-V 22.
"""
import importlib.util, os

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "memory_contracts", os.path.join(_HERE, "..", "..", "memory", "wp", "contracts.py"))
_mem = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mem)

A = "src/nvim/ascii_defs.h"
C = "src/nvim/charset.c"
PIECES = [
    (A, "ascii_iswhite", "3cbe82f79096229a84ed15445d03821a9ac36721a7b0f146bcc2e18c8566b0cf"),
    (A, "ascii_isdigit", "5b845db796c66d90ac8f620adfdddc3d3a92163afc231457cd0f3e4f24d6d9a9"),
    (A, "ascii_isxdigit", "dbbf1e2ae448d64b9d4d1378f96d2644f3043c0dc06dca16b54b1075b38aadb8"),
    (A, "ascii_isbdigit", "33b9593838e94fa19c89e2141836885eb99bbd331e41a42c230dd504d617afc4"),
    (C, "nr2hex", "150bb7c2c45bc242020a9915ec57e19eaae1a1b12343693d3d5e193c9c3354a4"),
    (C, "skipwhite", "cdb9e2ff70469688aebfaf0b0a03e4fb5b99fbdbbb16d29bd67f6a5b282eb390"),
    (C, "skipwhite_len", "095b625aada860ea19839c0843fecade163833eb677a163c4857ecca95b29677"),
    (C, "getwhitecols", "ae821bd0baa409303087bc7580c457e0bf4abbaffeb912e08ed304cdb41113f2"),
    (C, "skipdigits", "331e15d0b2890e3d0e3e0c68bb4009f7b8bc1eddf9bddd9cb932abd0b27cf33d"),
    (C, "skipbin", "4072a7d83562242e6701d8f5d08596ecc03411da48ff5e68a8589bf68a74946d"),
    (C, "skiphex", "88b61a8f5da97111e3b6bf779497066f861102172cc0044169ce47ab0c6f4535"),
    (C, "skiptodigit", "1faff32080a36e8e8342273e484d6f34c27141b36fc3e2a335258c904ae80f0e"),
    (C, "skiptobin", "cb4e67d773cfbf7ed5b9f1105942d24c46b7a4b7d9aecf02822a711455b214aa"),
    (C, "skiptohex", "be8244d8944f10865c50d07a2fee67816e6408b00087957a7027207ce6abd1d9"),
    (C, "skiptowhite", "d233a4cebdf38304f86e65f00653da184f5a0c4df700ed4d50ef349173b77edf"),
    (C, "skiptowhite_esc", "4638de3d7bb21571e39402033e9a70569eb8d70cbde3b97ba5eba467109a6fb1"),
    (C, "skip_to_newline", "e78272d9431aebc3cd1f1456ab95a361265b0753cac3d74665a66a2c2ffd7c70"),
    (C, "vim_isblankline", "d2bb364e8a81eec846cc0b0208242f6e6cf91b2da020bb152936ceac736bc3bb"),
    (C, "hex2nr", "d66d66c0b78f77634dfccc6519360b2f5f339bed097b061f7a577c265a1a058f"),
    (C, "hexhex2nr", "dd6d2ebf21928d49d2297ad89e39e7db9f2893b5d3226e245579be3d63cfd3da"),
    (C, "rem_backslash", "340908897327fca52d7f03f0ab809cb6fb0f5e82f3ad1600d1b1d66c42f22600"),
    (C, "backslash_halve", "f66254cb4705600597f9ee7f82123e5f2c9d7af00a29db5ad2a3281deffb0a2d"),
    (C, "backslash_halve_save", "364db9fd3127dfb86d6faf3df59819788726923302eaf97023fe69e75867f701"),
]

# xstrchrnul is proved in libraries/neovim/memory with exactly this contract (imported
# from there, so the two cannot drift); skip_to_newline calls it.
LOGIC = r"""
/*@ predicate is_white(integer c) = c == 32 || c == 9;
    predicate is_digit(integer c) = 48 <= c <= 57;
    predicate is_bdigit(integer c) = c == 48 || c == 49;
    predicate is_xdigit(integer c) = 48 <= c <= 57 || 65 <= c <= 70 || 97 <= c <= 102;
    // value of a hex digit (0..15)
    logic integer hexval(integer c) =
      48 <= c <= 57 ? c - 48 : (65 <= c <= 70 ? c - 55 : c - 87);
    // skiptowhite stops at ' ', TAB or NUL
    predicate is_stop(integer c) = c == 32 || c == 9 || c == 0;
    // skiptowhite_esc: a backslash or Ctrl-V escapes the next byte unless that is NUL
    predicate esc_at{L}(char *s, integer i) = (s[i] == 92 || s[i] == 22) && s[i + 1] != 0;
    // the positions where skiptowhite_esc looks for a stop: 0, then past one byte, or past
    // an escape pair. ewpos(s, j) is the j-th such position.
    logic integer ewpos{L}(char *s, integer j) =
      j <= 0 ? 0 : (esc_at(s, ewpos(s, j - 1)) ? ewpos(s, j - 1) + 2 : ewpos(s, j - 1) + 1);

    // backslash_halve (non-Windows rem_backslash): a backslash followed by a non-NUL
    // byte is dropped and the byte kept. Output byte k comes from input position bpos(s, k).
    predicate bs_at{L}(char *s, integer i) = s[i] == 92 && s[i + 1] != 0;
    logic integer bpos{L}(char *s, integer k) =
      k <= 0 ? 0 : (bs_at(s, bpos(s, k - 1)) ? bpos(s, k - 1) + 2 : bpos(s, k - 1) + 1);
    logic char bchar{L}(char *s, integer i) = bs_at(s, i) ? s[i + 1] : s[i];
*/
""" + f"""
/*@ {_mem.CONTRACTS["xstrchrnul"]} */
char *xstrchrnul(const char *str, char c);
"""

GHOST_PARAMS = {
    "skipwhite": ("char *skipwhite(const char *p)", "size_t n"),
    "getwhitecols": ("intptr_t getwhitecols(const char *p)", "size_t n"),
    "skipdigits": ("char *skipdigits(const char *q)", "size_t n"),
    "skipbin": ("const char *skipbin(const char *q)", "size_t n"),
    "skiphex": ("char *skiphex(char *q)", "size_t n"),
    "skiptodigit": ("char *skiptodigit(char *q)", "size_t n"),
    "skiptobin": ("const char *skiptobin(const char *q)", "size_t n"),
    "skiptohex": ("char *skiptohex(char *q)", "size_t n"),
    "skiptowhite": ("char *skiptowhite(const char *p)", "size_t n"),
    "skiptowhite_esc": ("char *skiptowhite_esc(const char *p)", "size_t n"),
    "vim_isblankline": ("bool vim_isblankline(char *lbuf)", "size_t n"),
    "backslash_halve": ("void backslash_halve(char *p)", "size_t n"),
    "backslash_halve_save": ("char *backslash_halve_save(const char *p)", "size_t n"),
}
GHOST_ARGS = {
    "getwhitecols": [("skipwhite(p)", "n")],
    "vim_isblankline": [("skipwhite(lbuf)", "n")],
    "backslash_halve_save": [("xmalloc(strlen(p) + 1)", "(char *)p, n")],
}


def span(x, pred):
    """x (a string of length n) starts with a run of bytes satisfying pred; the
    result points just past that run. pred(0) is false for every use."""
    return rf"""requires str_len((char *){x}, n);
    assigns \nothing;
    ensures \base_addr(\result) == \base_addr({x}) && {x} <= \result <= {x} + n;
    ensures !{pred}(*\result);
    ensures \forall char *r; \base_addr(r) == \base_addr({x}) && {x} <= r < \result ==> {pred}(*r);"""


def span_loop(var, x, pred):
    return [rf"""loop invariant \base_addr({var}) == \base_addr({x}) && {x} <= {var} <= {x} + n;
      loop invariant \forall char *r; \base_addr(r) == \base_addr({x}) && {x} <= r < {var} ==> {pred}(*r);
      loop assigns {var};
      loop variant n - ({var} - {x});"""]


CONTRACTS = {
    "ascii_iswhite": r"""assigns \nothing; ensures \result != 0 <==> is_white(c);""",
    "ascii_isdigit": r"""assigns \nothing; ensures \result != 0 <==> is_digit(c);""",
    "ascii_isxdigit": r"""assigns \nothing; ensures \result != 0 <==> is_xdigit(c);""",
    "ascii_isbdigit": r"""assigns \nothing; ensures \result != 0 <==> is_bdigit(c);""",
    # "Convert the lower 4 bits of n to its hex character", lower case letters.
    "nr2hex": r"""assigns \nothing;
    ensures \result == (n % 16 < 10 ? 48 + n % 16 : 97 + (n % 16 - 10));""",
    "skipwhite": span(r"\at(p, Pre)", "is_white").replace(r"\at(p, Pre)", "p"),
    "skipwhite_len": r"""requires \forall char *r; \base_addr(r) == \base_addr(p) && p <= r < p + len ==>
               (\forall char *q; \base_addr(q) == \base_addr(p) && p <= q < r ==> is_white(*q)) ==> \valid_read(r);
    assigns \nothing;
    ensures \base_addr(\result) == \base_addr(p) && p <= \result <= p + len;
    ensures \forall char *r; \base_addr(r) == \base_addr(p) && p <= r < \result ==> is_white(*r);
    ensures \result < p + len ==> !is_white(*\result);""",
    "getwhitecols": r"""requires str_len((char *)p, n);
    assigns \nothing;
    ensures 0 <= \result <= n && !is_white(p[\result]);
    ensures \forall integer j; 0 <= j < \result ==> is_white(p[j]);""",
    "skipdigits": span("q", "is_digit"),
    "skipbin": span("q", "is_bdigit"),
    "skiphex": span("q", "is_xdigit"),
    "skiptodigit": span("q", "not_digit"),
    "skiptobin": span("q", "not_bdigit"),
    "skiptohex": span("q", "not_xdigit"),
    "skiptowhite": span("p", "not_stop"),
    "skiptowhite_esc": r"""requires str_len((char *)p, n);
    assigns \nothing;
    ensures \base_addr(\result) == \base_addr(p) && p <= \result <= p + n;
    // the first stop among the walk positions
    ensures \exists integer j; 0 <= j <= n && \result == p + ewpos((char *)p, j) && is_stop(*\result)
              && \forall integer i; 0 <= i < j ==> !is_stop(p[ewpos((char *)p, i)]);""",
    "skip_to_newline": r"""requires is_str((char *)p);
    assigns \nothing;
    ensures \exists integer i; 0 <= i && \result == p + i && (p[i] == 10 || p[i] == 0)
            && \forall integer j; 0 <= j < i ==> p[j] != 10 && p[j] != 0;""",
    "vim_isblankline": r"""requires str_len(lbuf, n);
    assigns \nothing;
    // the first byte that is not ' ' or TAB (one exists: the NUL at lbuf[n])
    ensures \forall char *r; \base_addr(r) == \base_addr(lbuf) && lbuf <= r <= lbuf + n && !is_white(*r)
              && (\forall char *q; \base_addr(q) == \base_addr(lbuf) && lbuf <= q < r ==> is_white(*q)) ==>
              (\result != 0 <==> (*r == 0 || *r == 13 || *r == 10));""",
    # "Only valid when the argument is '0' - '9', 'A' - 'F' or 'a' - 'f'": the value for
    # those; for any other value no undefined behavior (every char and every int above
    # INT_MIN + 47).
    "hex2nr": r"""requires c >= -2147483648 + 48;
    assigns \nothing;
    ensures is_xdigit(c) ==> \result == hexval(c);""",
    "hexhex2nr": r"""requires \valid_read(p) && (is_xdigit(p[0]) ==> \valid_read(p + 1));
    assigns \nothing;
    ensures is_xdigit(p[0]) && is_xdigit(p[1]) ==> \result == 16 * hexval(p[0]) + hexval(p[1]);
    ensures !(is_xdigit(p[0]) && is_xdigit(p[1])) ==> \result == -1;""",
    "rem_backslash": r"""requires \valid_read(str) && (str[0] == 92 ==> \valid_read(str + 1));
    assigns \nothing;
    ensures \result != 0 <==> str[0] == 92 && str[1] != 0;""",
    "backslash_halve": r"""requires str_len(p, n) && \valid(p + (0 .. n));
    assigns p[0 .. n];
    ensures \exists integer m; 0 <= m <= n && bpos{Pre}(p, m) == n && p[m] == 0
            && \forall integer k; 0 <= k < m ==>
                 bpos{Pre}(p, k) < n && p[k] == bchar{Pre}(p, bpos{Pre}(p, k));""",
    "backslash_halve_save": r"""requires str_len((char *)p, n) && n < 9223372036854775807;
    requires vp_live < 2147483647;
    // no assigns clause: the new block is not nameable before the call. The input
    // string is unchanged (next line), and only vp_live/vp_last change among globals.
    ensures \forall integer i; 0 <= i <= n ==> p[i] == \old(p[i]);
    ensures vp_live == \old(vp_live) + 1 && vp_last == \result && \valid(\result + (0 .. n));
    ensures \exists integer m; 0 <= m <= n && bpos{Pre}((char *)p, m) == n && \result[m] == 0
            && \forall integer k; 0 <= k < m ==>
                 bpos{Pre}((char *)p, k) < n && \result[k] == bchar{Pre}((char *)p, bpos{Pre}((char *)p, k));""",
}
LOGIC += r"""
/*@ predicate not_digit(integer c) = c != 0 && !is_digit(c);
    predicate not_bdigit(integer c) = c != 0 && !is_bdigit(c);
    predicate not_xdigit(integer c) = c != 0 && !is_xdigit(c);
    predicate not_stop(integer c) = !is_stop(c);
*/
"""

LOOPS = {
    "skipwhite": [("  while (ascii_iswhite(*p)) {", span_loop("p", r"\at(p, Pre)", "is_white")[0])],
    "skipwhite_len": [("  for (; len > 0 && ascii_iswhite(*p); len--) {",
        r"""loop invariant 0 <= len <= \at(len, Pre) && p - \at(p, Pre) == \at(len, Pre) - len;
      loop invariant \base_addr(p) == \base_addr(\at(p, Pre));
      loop invariant \forall char *r; \base_addr(r) == \base_addr(p) && \at(p, Pre) <= r < p ==> is_white(*r);
      loop assigns p, len;
      loop variant len;""")],
    "skipdigits": [("  while (ascii_isdigit(*p)) {", span_loop("p", "q", "is_digit")[0])],
    "skipbin": [("  while (ascii_isbdigit(*p)) {", span_loop("p", "q", "is_bdigit")[0])],
    "skiphex": [("  while (ascii_isxdigit(*p)) {", span_loop("p", "q", "is_xdigit")[0])],
    "skiptodigit": [("  while (*p != NUL && !ascii_isdigit(*p)) {", span_loop("p", "q", "not_digit")[0])],
    "skiptobin": [("  while (*p != NUL && !ascii_isbdigit(*p)) {", span_loop("p", "q", "not_bdigit")[0])],
    "skiptohex": [("  while (*p != NUL && !ascii_isxdigit(*p)) {", span_loop("p", "q", "not_xdigit")[0])],
    "skiptowhite": [("  while (*p != ' ' && *p != '\\t' && *p != NUL) {",
                     span_loop("p", r"\at(p, Pre)", "not_stop")[0])],
    "skiptowhite_esc": [("  while (*p != ' ' && *p != '\\t' && *p != NUL) {", "ghost size_t j = 0;"),
        ("  while (*p != ' ' && *p != '\\t' && *p != NUL) {",
        r"""loop invariant \base_addr(p) == \base_addr(\at(p, Pre)) && \at(p, Pre) <= p <= \at(p, Pre) + n;
      loop invariant 0 <= j <= p - \at(p, Pre) && p - \at(p, Pre) == ewpos((char *)\at(p, Pre), j);
      loop invariant \forall integer i; 0 <= i < j ==> !is_stop(\at(p, Pre)[ewpos((char *)\at(p, Pre), i)]);
      loop assigns p, j;
      loop variant n - (p - \at(p, Pre));"""),
        ("    p++;\n  }\n  return (char *)p;", "ghost j++;")],
    "backslash_halve": [
        ("  for (; *p && !rem_backslash(p); p++) {}",
         r"""loop invariant \base_addr(p) == \base_addr(\at(p, Pre)) && \at(p, Pre) <= p <= \at(p, Pre) + n;
      loop invariant \forall integer k; 0 <= k <= p - \at(p, Pre) ==> bpos{Pre}(\at(p, Pre), k) == k;
      loop invariant \forall integer k; 0 <= k < p - \at(p, Pre) ==> !bs_at{Pre}(\at(p, Pre), k);
      loop assigns p;
      loop variant n - (p - \at(p, Pre));"""),
        ("    *dst++ = *(p + 1);\n    p += 2;\n",
         r"""assert bs_at{Pre}(\at(p, Pre), p - \at(p, Pre)) && dst == p &&
        bpos{Pre}(\at(p, Pre), dst - \at(p, Pre) + 1) == p - \at(p, Pre) + 2 &&
        bchar{Pre}(\at(p, Pre), p - \at(p, Pre)) == *(p + 1);"""),
        ("start:\n        *dst++ = *(p + 1);",
         r"""assert bs_at{Pre}(\at(p, Pre), p - \at(p, Pre)) &&
        bpos{Pre}(\at(p, Pre), dst - \at(p, Pre) + 1) == p - \at(p, Pre) + 2 &&
        bchar{Pre}(\at(p, Pre), p - \at(p, Pre)) == *(p + 1);"""),
        ("        *dst++ = *p++;",
         r"""assert !bs_at{Pre}(\at(p, Pre), p - \at(p, Pre)) &&
        bpos{Pre}(\at(p, Pre), dst - \at(p, Pre) + 1) == p - \at(p, Pre) + 1 &&
        bchar{Pre}(\at(p, Pre), p - \at(p, Pre)) == *p;"""),
        ("    *dst = NUL;\n  }\n}",
         r"""assert \let q = p; \at(*q, Pre) == 0; */
    /*@ assert p == \at(p, Pre) + n && bpos{Pre}(\at(p, Pre), dst - \at(p, Pre)) == n
        && 0 <= dst - \at(p, Pre) <= n;"""),
        ("    while (*p != NUL) {",
         r"""loop invariant \base_addr(p) == \base_addr(\at(p, Pre)) && \base_addr(dst) == \base_addr(p);
      loop invariant \at(p, Pre) <= dst <= p <= \at(p, Pre) + n;
      loop invariant bpos{Pre}(\at(p, Pre), dst - \at(p, Pre)) == p - \at(p, Pre);
      loop invariant \forall integer i; p - \at(p, Pre) <= i <= n ==> \at(p, Pre)[i] == \at(\at(p, Pre)[i], Pre);
      loop invariant \forall integer k; 0 <= k < dst - \at(p, Pre) ==>
        bpos{Pre}(\at(p, Pre), k) < p - \at(p, Pre) && \at(p, Pre)[k] == bchar{Pre}(\at(p, Pre), bpos{Pre}(\at(p, Pre), k));
      loop assigns p, dst, \at(p, Pre)[0 .. n];
      loop variant n - (p - \at(p, Pre));"""),
    ],
    "backslash_halve_save": [("  char *dst = res;", r"""assert sep: \separated(res + (0 .. n), p + (0 .. n));"""), ("  while (*p != NUL) {",
        r"""loop invariant \base_addr(p) == \base_addr(\at(p, Pre)) && \at(p, Pre) <= p <= \at(p, Pre) + n;
      loop invariant \base_addr(dst) == \base_addr(res) && res <= dst <= res + (p - \at(p, Pre));
      loop invariant \forall integer i; 0 <= i <= n ==> \at(p, Pre)[i] == \at(\at(p, Pre)[i], Pre);
      loop invariant vp_last == (void *)res && vp_live == \at(vp_live, Pre) + 1;
      loop invariant bpos{Pre}((char *)\at(p, Pre), dst - res) == p - \at(p, Pre);
      loop invariant \forall integer k; 0 <= k < dst - res ==>
        bpos{Pre}((char *)\at(p, Pre), k) < p - \at(p, Pre)
        && res[k] == bchar{Pre}((char *)\at(p, Pre), bpos{Pre}((char *)\at(p, Pre), k));
      loop assigns p, dst, res[0 .. n];
      loop variant n - (p - \at(p, Pre));"""),
        ("      *dst++ = *(p + 1);", r"""assert bs_at{Pre}((char *)\at(p, Pre), p - \at(p, Pre)) &&
        bpos{Pre}((char *)\at(p, Pre), dst - res + 1) == p - \at(p, Pre) + 2 &&
        bchar{Pre}((char *)\at(p, Pre), p - \at(p, Pre)) == *(p + 1);"""),
        ("      *dst++ = *p++;", r"""assert !bs_at{Pre}((char *)\at(p, Pre), p - \at(p, Pre)) &&
        bpos{Pre}((char *)\at(p, Pre), dst - res + 1) == p - \at(p, Pre) + 1 &&
        bchar{Pre}((char *)\at(p, Pre), p - \at(p, Pre)) == *p;""")],
}
