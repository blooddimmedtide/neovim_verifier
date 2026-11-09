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
    "backslash_halve_save": [("xmalloc(strlen(p) + 1)", "(char *)p, n + 1")],
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

# ---------------------------------------------------------------------------
# vim_str2nr (and ascii_isodigit, which it calls)
# ---------------------------------------------------------------------------
PIECES[PIECES.index((A, "ascii_isbdigit", "33b9593838e94fa19c89e2141836885eb99bbd331e41a42c230dd504d617afc4")) + 1:1] = [
    (A, "ascii_isodigit", "f3a656dd46f200517f27fce990e896055ef8cd1fe26d852a2e8a4e90363c3107")]
PIECES.append((C, "vim_str2nr", "96c8941996e2dd27f7a62803003ba97822750366c2106cabbc43cbd9e32ceb1c"))
# fixed fork (verified_neovim): vim_str2nr stops at INT_MAX characters when maxlen == 0
FIXED_SHA = {"vim_str2nr": "c39da480804d55fab77e37bb716e8e9a31666d7760f05aadb95932bd70fed935"}

# Copies of Neovim's definitions (each line is checked against upstream by PRELUDE_CHECKS).
PRELUDE_EXTRA = r"""#include <limits.h>
typedef int64_t varnumber_T;
typedef uint64_t uvarnumber_T;
#define VARNUMBER_MAX INT64_MAX
#define UVARNUMBER_MAX UINT64_MAX
#define VARNUMBER_MIN INT64_MIN
#define ASCII_ISLOWER(c) ((unsigned)(c) >= 'a' && (unsigned)(c) <= 'z')
#define ASCII_ISUPPER(c) ((unsigned)(c) >= 'A' && (unsigned)(c) <= 'Z')
#define ASCII_ISALPHA(c) (ASCII_ISUPPER(c) || ASCII_ISLOWER(c))
#define ASCII_ISALNUM(c) (ASCII_ISALPHA(c) || ascii_isdigit(c))
#define FUNC_ATTR_NONNULL_ARG(x)
typedef enum {
  STR2NR_DEC = 0,
  STR2NR_BIN = (1 << 0),
  STR2NR_OCT = (1 << 1),
  STR2NR_HEX = (1 << 2),
  STR2NR_OOCT = (1 << 3),
  STR2NR_FORCE = (1 << 7),
  STR2NR_ALL = STR2NR_BIN | STR2NR_OCT | STR2NR_HEX | STR2NR_OOCT,
  STR2NR_NO_OCT = STR2NR_BIN | STR2NR_HEX | STR2NR_OOCT,
  STR2NR_QUOTE = (1 << 4),
} ChStr2NrFlags;
// abort() must be unreachable: its precondition is false, so WP must prove each call dead.
/*@ requires \false; assigns \nothing; ensures \false; */
void abort(void);
static inline bool ascii_isdigit(int c);
"""
PRELUDE_CHECKS = [
    ("src/nvim/eval/typval_defs.h", "typedef int64_t varnumber_T;"),
    ("src/nvim/eval/typval_defs.h", "typedef uint64_t uvarnumber_T;"),
    ("src/nvim/eval/typval_defs.h", "#define VARNUMBER_MAX INT64_MAX"),
    ("src/nvim/eval/typval_defs.h", "#define UVARNUMBER_MAX UINT64_MAX"),
    ("src/nvim/eval/typval_defs.h", "#define VARNUMBER_MIN INT64_MIN"),
    ("src/nvim/macros_defs.h", "#define ASCII_ISLOWER(c) ((unsigned)(c) >= 'a' && (unsigned)(c) <= 'z')"),
    ("src/nvim/macros_defs.h", "#define ASCII_ISUPPER(c) ((unsigned)(c) >= 'A' && (unsigned)(c) <= 'Z')"),
    ("src/nvim/macros_defs.h", "#define ASCII_ISALPHA(c) (ASCII_ISUPPER(c) || ASCII_ISLOWER(c))"),
    ("src/nvim/macros_defs.h", "#define ASCII_ISALNUM(c) (ASCII_ISALPHA(c) || ascii_isdigit(c))"),
    ("src/nvim/charset.h", "  STR2NR_BIN = (1 << 0),  ///< Allow binary numbers."),
    ("src/nvim/charset.h", "  STR2NR_OCT = (1 << 1),  ///< Allow octal numbers."),
    ("src/nvim/charset.h", "  STR2NR_HEX = (1 << 2),  ///< Allow hexadecimal numbers."),
    ("src/nvim/charset.h", "  STR2NR_OOCT = (1 << 3),  ///< Octal with prefix \"0o\": 0o777"),
    ("src/nvim/charset.h", "  STR2NR_FORCE = (1 << 7),"),
    ("src/nvim/charset.h", "  STR2NR_ALL = STR2NR_BIN | STR2NR_OCT | STR2NR_HEX | STR2NR_OOCT,"),
    ("src/nvim/charset.h", "  STR2NR_NO_OCT = STR2NR_BIN | STR2NR_HEX | STR2NR_OOCT,"),
    ("src/nvim/charset.h", "  STR2NR_QUOTE = (1 << 4),  ///< Ignore embedded single quotes."),
]

# The number syntax, from the doc comment and ChStr2NrFlags (not from the code):
#  - an optional '-' (a0 = 1), then an optional prefix, then digits of the base;
#  - FORCE: the base is fixed by the flags, a matching 0x/0b/0o prefix followed by a digit
#    of the base is skipped; prep is 0;
#  - otherwise, with any of HEX/BIN/OOCT/OCT allowed, "0" followed by not 8/9: 0x/0X + hex
#    digit is hex, 0b/0B + binary digit is binary, 0o/0O + octal digit is octal (these
#    return the letter in prep), "0" + octal digits only (up to the first non-digit) is old
#    octal (prep '0'); everything else decimal (prep 0);
#  - QUOTE: a ' after the first digit position that is followed by a digit is skipped;
#  - the value saturates at UVARNUMBER_MAX (overflow set);
#  - "available" positions: before maxlen, or (maxlen == 0) before INT_MAX, the most an int
#    length can report. Upstream only meets this below 2 GiB (its precondition).
LOGIC += r"""
/*@ predicate av(integer ml, integer i) = ml == 0 ? i < 2147483647 : i < ml;
    predicate is_odigit(integer c) = 48 <= c <= 55;
    predicate is_alnum(integer c) = 48 <= c <= 57 || 65 <= c <= 90 || 97 <= c <= 122;
    predicate isdig(integer b, integer c) =
      b == 2 ? is_bdigit(c) : (b == 8 ? is_odigit(c) : (b == 10 ? is_digit(c) : is_xdigit(c)));
    logic integer a0{L}(char *s) = s[0] == 45 ? 1 : 0;
    predicate pfx{L}(char *s, integer ml, integer c1, integer c2, integer b) =
      av(ml, a0(s) + 2) && s[a0(s)] == 48 && (s[a0(s) + 1] == c1 || s[a0(s) + 1] == c2)
      && isdig(b, s[a0(s) + 2]);
    // the quote flag as a separate term (WP's simplifier otherwise rewrites what & 16 to 16
    // in some places and not others, and the provers cannot match the two)
    logic integer qf(integer what) = (what & 16) != 0 ? 1 : 0;
    // what & ~(STR2NR_FORCE | STR2NR_QUOTE): with the precondition (0 <= what <= 255, bits 32
    // and 64 clear) that is what & 15. Lemma mask_lo links it to the mask WP derives from the code.
    logic integer kind(integer what) = what & 15;
    predicate forced(integer what) = (what & 128) != 0;
    predicate oct_ok{L}(char *s, integer ml, integer j) =
      \forall integer k; j <= k ==> (\forall integer m; j <= m <= k ==> av(ml, m) && is_digit(s[m])) ==> s[k] <= 55;
    predicate c0{L}(char *s, integer ml, integer what) =
      (what & 15) != 0 && av(ml, a0(s) + 1) && s[a0(s)] == 48 && s[a0(s) + 1] != 56 && s[a0(s) + 1] != 57;
    // unforced prefix detection, in the code's order: 16 = 0x, 2 = 0b, 9 = 0o, 8 = old octal, 10 = none.
    // One flat if-chain (no predicate refers to another): nested definitions blow up WP's simplifier.
    logic integer cls{L}(char *s, integer ml, integer what) =
      !c0(s, ml, what) ? 10 :
      (((what & 4) != 0 && pfx(s, ml, 120, 88, 16)) ? 16 :
      (((what & 1) != 0 && pfx(s, ml, 98, 66, 2)) ? 2 :
      (((what & 8) != 0 && pfx(s, ml, 111, 79, 8)) ? 9 :
      (((what & 2) != 0 && is_odigit(s[a0(s) + 1]) && oct_ok(s, ml, a0(s) + 2)) ? 8 : 10))));
    logic integer nbase{L}(char *s, integer ml, integer what) =
      forced(what) ? (kind(what) == 4 ? 16 : (kind(what) == 1 ? 2 : (kind(what) == 0 ? 10 : 8)))
      : (cls(s, ml, what) == 9 ? 8 : cls(s, ml, what));
    logic integer nskip{L}(char *s, integer ml, integer what) =
      forced(what) ?
        (((kind(what) == 4 && pfx(s, ml, 120, 88, 16)) || (kind(what) == 1 && pfx(s, ml, 98, 66, 2))
          || ((kind(what) == 2 || kind(what) == 8 || kind(what) == 10) && pfx(s, ml, 111, 79, 8))) ? 2 : 0)
      : ((cls(s, ml, what) == 16 || cls(s, ml, what) == 2 || cls(s, ml, what) == 9) ? 2 : 0);
    logic integer npre{L}(char *s, integer ml, integer what) =
      forced(what) ? 0 : ((cls(s, ml, what) == 16 || cls(s, ml, what) == 2 || cls(s, ml, what) == 9) ? (unsigned char)s[a0(s) + 1]
                          : (cls(s, ml, what) == 8 ? 48 : 0));

    // digit positions from p0, skipping a quote that sits between two digits (q != 0)
    predicate qskip{L}(char *s, integer ml, integer q, integer b, integer p0, integer k) =
      q != 0 && k > p0 && av(ml, k) && s[k] == 39 && av(ml, k + 1) && isdig(b, s[k + 1]);
    logic integer dp{L}(char *s, integer ml, integer q, integer b, integer p0, integer j) =
      j <= 0 ? p0 :
        (qskip(s, ml, q, b, p0, dp(s, ml, q, b, p0, j - 1) + 1) ? dp(s, ml, q, b, p0, j - 1) + 2
                                                                  : dp(s, ml, q, b, p0, j - 1) + 1);
    // where the scan for digit j starts (before a quote skip)
    logic integer rawp{L}(char *s, integer ml, integer q, integer b, integer p0, integer j) =
      j <= 0 ? p0 : dp(s, ml, q, b, p0, j - 1) + 1;
    predicate okd{L}(char *s, integer ml, integer q, integer b, integer p0, integer j) =
      av(ml, dp(s, ml, q, b, p0, j)) && isdig(b, s[dp(s, ml, q, b, p0, j)]);
    logic integer dval{L}(char *s, integer ml, integer q, integer b, integer p0, integer j) =
      j <= 0 ? 0 : b * dval(s, ml, q, b, p0, j - 1) + hexval(s[dp(s, ml, q, b, p0, j - 1)]);
    predicate ndig{L}(char *s, integer ml, integer q, integer b, integer p0, integer m) =
      0 <= m && (\forall integer j; 0 <= j < m ==> okd(s, ml, q, b, p0, j)) && !okd(s, ml, q, b, p0, m);
    logic integer sat(integer v) = v > 18446744073709551615 ? 18446744073709551615 : v;
*/
"""

_S2N = r"(char *)start, maxlen"
_ARGS = r"(char *)start, maxlen, qf(what), nbase{Pre}((char *)start, maxlen, what), a0{Pre}((char *)start) + nskip{Pre}((char *)start, maxlen, what)"
_FIRST = rf"\forall integer m; ndig{{Pre}}({_ARGS}, m) ==>"
_E = rf"dp{{Pre}}({_ARGS}, m)"
_V = rf"dval{{Pre}}({_ARGS}, m)"
_FAIL = rf"(strict != 0 && {_E} != maxlen && is_alnum(\at(start[{_E}], Pre)))"
_NEG = r"\at(start[0], Pre) == 45"
CONTRACTS["ascii_isodigit"] = r"""assigns \nothing; ensures \result != 0 <==> is_odigit(c);"""
CONTRACTS["vim_str2nr"] = rf"""requires maxlen >= 0;
    requires maxlen > 0 ==> \valid_read(start + (0 .. maxlen - 1));
    requires maxlen == 0 ==> str_len((char *)start, n);
    requires maxlen > 0 || n < 2147483647;   // upstream only: the bug needs a number of 2 GiB characters
    requires 0 <= what <= 255 && (what & 96) == 0;   // what is a set of STR2NR_* flags (every caller)
    requires forced(what) ==> kind(what) \in {{0, 1, 2, 4, 8, 10}};   // else abort(); no caller passes that
    requires prep != \null ==> \valid(prep);
    requires len != \null ==> \valid(len);
    requires nptr != \null ==> \valid(nptr);
    requires unptr != \null ==> \valid(unptr);
    requires overflow != \null ==> \valid(overflow);
    requires \separated(start + (0 .. (maxlen > 0 ? maxlen - 1 : n)), prep, len, nptr, unptr, overflow);
    requires prep != \null && len != \null ==> \separated(prep, len);
    requires prep != \null && nptr != \null ==> \separated(prep, nptr);
    requires prep != \null && unptr != \null ==> \separated(prep, unptr);
    requires prep != \null && overflow != \null ==> \separated(prep, overflow);
    requires len != \null && nptr != \null ==> \separated(len, nptr);
    requires len != \null && unptr != \null ==> \separated(len, unptr);
    requires len != \null && overflow != \null ==> \separated(len, overflow);
    requires nptr != \null && unptr != \null ==> \separated(nptr, unptr);
    requires nptr != \null && overflow != \null ==> \separated(nptr, overflow);
    requires unptr != \null && overflow != \null ==> \separated(unptr, overflow);
    assigns *prep, *len, *nptr, *unptr, *overflow;
    ensures digits_exist: \exists integer m; ndig{{Pre}}({_ARGS}, m);
    ensures length: len != \null ==> {_FIRST} *len == ({_FAIL} ? 0 : {_E});
    ensures prep: prep != \null ==> {_FIRST}
              *prep == ({_FAIL} ? \old(*prep) : npre{{Pre}}({_S2N}, what));
    ensures signed: nptr != \null ==> {_FIRST}
              *nptr == ({_FAIL} ? \old(*nptr) :
                        ({_NEG} ? (sat({_V}) > 9223372036854775807 ? -9223372036854775808 : -sat({_V}))
                                : (sat({_V}) > 9223372036854775807 ? 9223372036854775807 : sat({_V}))));
    ensures unsigned: unptr != \null ==> {_FIRST}
              *unptr == ({_FAIL} ? \old(*unptr) :
                         ((nptr != \null && !({_NEG}) && sat({_V}) > 9223372036854775807) ? 9223372036854775807 : sat({_V})));
    ensures overflow: overflow != \null ==> {_FIRST}
              (*overflow != 0 <==> (\old(*overflow) != 0 || {_V} > 18446744073709551615
                 || (!{_FAIL} && nptr != \null && sat({_V}) > 9223372036854775807)));"""

_PARSE = [  # (label, base) in the order of the four expanded PARSE_NUMBER uses
    ("vim_str2nr_bin", 2), ("vim_str2nr_oct", 8), ("vim_str2nr_dec", 10), ("vim_str2nr_hex", 16)]
_BND = r"(maxlen > 0 ? maxlen : n)"
_LARGS = r"(char *)start, maxlen, qf(what), " + "{b}" + r", after_prefix - start"


def _parse_loop(b):
    la = _LARGS.format(b=b)
    return rf"""loop invariant nbase{{Pre}}((char *)start, maxlen, what) == {b};
      loop invariant after_prefix - start == a0{{Pre}}((char *)start) + nskip{{Pre}}((char *)start, maxlen, what);
      loop invariant \base_addr(ptr) == \base_addr(start) && after_prefix <= ptr && ptr - start <= {_BND};
      loop invariant 0 <= gj <= ptr - after_prefix;
      loop invariant ptr - start == rawp{{Pre}}({la}, gj)
        || (ptr - start == dp{{Pre}}({la}, gj) && qskip{{Pre}}({la}, rawp{{Pre}}({la}, gj)));
      loop invariant \forall integer j; 0 <= j < gj ==> okd{{Pre}}({la}, j);
      loop invariant un == sat(dval{{Pre}}({la}, gj));
      loop invariant overflow != \null ==> (*overflow != 0 <==> (\at(*overflow, Pre) != 0 || dval{{Pre}}({la}, gj) > 18446744073709551615));
      loop assigns ptr, un, gj, *overflow;
      loop variant {_BND} + 1 - (ptr - start);"""


_P0 = r"a0{Pre}((char *)start) + nskip{Pre}((char *)start, maxlen, what)"


def _helper(b):
    la = rf"(char *)start, maxlen, qf(what), {b}, {_P0}"
    return rf"""requires maxlen >= 0;
    requires maxlen > 0 ==> \valid_read(start + (0 .. maxlen - 1));
    requires maxlen == 0 ==> str_len((char *)start, n);
    requires maxlen > 0 || n < 2147483647;   // upstream only: as vim_str2nr's
    requires 0 <= what <= 255;
    requires \valid(pptr) && \valid(pun) && \separated(pptr, pun);
    requires \separated(start + (0 .. {_BND}), pptr, pun);
    requires overflow != \null ==> \valid(overflow) && \separated(overflow, pptr, pun)
             && \separated(start + (0 .. {_BND}), overflow);
    requires h_base: nbase((char *)start, maxlen, what) == {b};
    requires h_pos: \base_addr(*pptr) == \base_addr(start) && *pptr - start == a0((char *)start) + nskip((char *)start, maxlen, what);
    requires h_zero: *pun == 0;
    assigns *pptr, *pun, *overflow;
    ensures \exists integer m; ndig{{Pre}}({la}, m);
    ensures \forall integer m; ndig{{Pre}}({la}, m) ==>
      \base_addr(*pptr) == \base_addr(start) && *pptr - start == dp{{Pre}}({la}, m) && *pptr - start <= {_BND}
      && *pun == sat(dval{{Pre}}({la}, m))
      && (overflow != \null ==> (*overflow != 0 <==> (\old(*overflow) != 0 || dval{{Pre}}({la}, m) > 18446744073709551615)));"""


# The four digit loops are in the helpers tool_patches.outline_str2nr makes (vp_parse_<base>),
# in the order of _PARSE; each helper gets its contract, a ghost digit counter gj, the loop
# invariants and the gj increment.
LOOPS["vim_str2nr"] = [
    ("  int pre = 0;  // default is decimal", "ghost int gi = 2;"),   # copy of the octal check's i
    # the prefix detection, step by step (which class cls() the code has found)
    ("    // Detect old octal format: 0 followed by octal digits.\n    pre = 0;\n",
     r"assert no_prefix: c0{Pre}((char *)start, maxlen, what) && (cls{Pre}((char *)start, maxlen, what) == 8 || cls{Pre}((char *)start, maxlen, what) == 10);", None, "after"),
    ("      goto vim_str2nr_dec;\n    }\n", r"assert not_old_octal: cls{Pre}((char *)start, maxlen, what) == 10;"),
    ("        goto vim_str2nr_dec;\n      }", r"assert digits_so_far: \forall integer m; a0{Pre}((char *)start) + 2 <= m <= a0{Pre}((char *)start) + i ==> av(maxlen, m) && is_digit(\at(start[m], Pre));"),
    ("        goto vim_str2nr_dec;\n      }", r"assert digit_8_or_9: !oct_ok{Pre}((char *)start, maxlen, a0{Pre}((char *)start) + 2) && cls{Pre}((char *)start, maxlen, what) == 10;"),
    ("    }\n    pre = '0';\n    goto vim_str2nr_oct;", "ghost gi++;"),
    ("    pre = '0';\n    goto vim_str2nr_oct;", r"assert octal_end: \let g = gi; !(av(maxlen, a0{Pre}((char *)start) + g) && is_digit(\at(start[a0{Pre}((char *)start) + g], Pre))) && \forall integer k; a0{Pre}((char *)start) + 2 <= k < a0{Pre}((char *)start) + g ==> \at(start[k], Pre) <= 55;"),
    ("    pre = '0';\n    goto vim_str2nr_oct;", r"assert old_octal: oct_ok{Pre}((char *)start, maxlen, a0{Pre}((char *)start) + 2) && cls{Pre}((char *)start, maxlen, what) == 8;"),
    ("    goto vim_str2nr_dec;\n  }\n", r"assert no_zero: !c0{Pre}((char *)start, maxlen, what) && cls{Pre}((char *)start, maxlen, what) == 10;"),
    ("    for (int i = 2; !STRING_ENDED(ptr + i) && ascii_isdigit(ptr[i]); i++) {",
     rf"""loop invariant 2 <= i && a0{{Pre}}((char *)start) + i <= {_BND} + 1 && ptr - start == a0{{Pre}}((char *)start) && gi == i;
      loop invariant \forall integer k; a0{{Pre}}((char *)start) + 2 <= k < a0{{Pre}}((char *)start) + i ==>
        av(maxlen, k) && is_digit(\at(start[k], Pre)) && \at(start[k], Pre) <= 55;
      loop assigns i, gi;
      loop variant {_BND} + 1 - i;"""),
] + [(f"static void vp_parse_{lab[11:]}(", _helper(b)) for lab, b in _PARSE] \
  + [("  uvarnumber_T un = *pun;\n", "ghost size_t gj = 0;", k, "after") for k in range(4)] \
  + [("    while (!STRING_ENDED(ptr)) {", _parse_loop(b), k) for k, (_, b) in enumerate(_PARSE)] \
  + [("      ptr++;\n    }\n  } while (0);", "ghost gj++;", k) for k in range(4)] \
  + [("        ptr++;\n        if (!STRING_ENDED(ptr) && ", "assert quote_bit: qf(what) == 1;", k) for k in range(4)] \
  + [("      ptr++;\n    }\n  } while (0);", rf"assert next: gj >= 1 && rawp{{Pre}}({_LARGS.format(b=b)}, gj) == dp{{Pre}}({_LARGS.format(b=b)}, gj - 1) + 1;", k)
     for k, (_, b) in enumerate(_PARSE)] \
  + [("      if ((what & STR2NR_QUOTE) && ptr > after_prefix && *ptr == '\\'') {", rf"assert unfold: dp{{Pre}}({_LARGS.format(b=b)}, gj) == (gj <= 0 ? after_prefix - start : (qskip{{Pre}}({_LARGS.format(b=b)}, rawp{{Pre}}({_LARGS.format(b=b)}, gj)) ? rawp{{Pre}}({_LARGS.format(b=b)}, gj) + 1 : rawp{{Pre}}({_LARGS.format(b=b)}, gj))) && (gj <= 0 ==> rawp{{Pre}}({_LARGS.format(b=b)}, gj) == after_prefix - start);", k)
     for k, (_, b) in enumerate(_PARSE)] \
  + [("      const uvarnumber_T digit = ", rf"assert ptr - start == dp{{Pre}}({_LARGS.format(b=b)}, gj) && okd{{Pre}}({_LARGS.format(b=b)}, gj);", k)
     for k, (_, b) in enumerate(_PARSE)] \
  + [("          continue;", rf"assert ptr - start == dp{{Pre}}({_LARGS.format(b=b)}, gj) && qskip{{Pre}}({_LARGS.format(b=b)}, rawp{{Pre}}({_LARGS.format(b=b)}, gj));", k)
     for k, (_, b) in enumerate(_PARSE)] \
  + [("#undef STRING_ENDED\n  *pptr = ptr;", rf"assert ndig{{Pre}}((char *)start, maxlen, qf(what), {b}, {_P0}, gj) && \forall integer m; ndig{{Pre}}((char *)start, maxlen, qf(what), {b}, {_P0}, m) ==> m == gj;", k)
     for k, (_, b) in enumerate(_PARSE)]

GHOST_PARAMS["vim_str2nr"] = [(
    "void vim_str2nr(const char *const start, int *const prep, int *const len, const int what,\n"
    "                varnumber_T *const nptr, uvarnumber_T *const unptr, const int maxlen,\n"
    "                const bool strict, bool *const overflow)", "size_t n")] + [
    (__import__("tool_patches").HELPER_SIG.format(lab=lab[11:]), "size_t n") for lab, _ in _PARSE]
GHOST_ARGS["vim_str2nr"] = [(__import__("tool_patches").HELPER_CALL.format(lab=lab[11:]), "n") for lab, _ in _PARSE]

# ---------------------------------------------------------------------------
# try_getdigits / getdigits / getdigits_int / getdigits_long / getdigits_int32
# strtoimax's contract is in stubs/vp_strtoimax.h. Configuration: x86_64 Linux
# (SIZEOF_INT 4, SIZEOF_LONG 8, SIZEOF_INTMAX_T 8) with asserts enabled, as in Neovim's
# RelWithDebInfo builds (CMakeLists.txt turns -DNDEBUG into -DRELDEBUG).
# ---------------------------------------------------------------------------
PIECES += [
    (C, "try_getdigits", "06b9277a84c09ace2d083bba6029a51dc8f653844d1b1b4a1c361273ef8b4d76"),
    (C, "getdigits", "da8e75625cdd598b0d68e71c1d5cbfbfb5279463979c8fc707f6a55555dbcbb9"),
    (C, "getdigits_int", "c27194f9728df5184ba11a1270c71c5d5618ee95708aa3e678aa4b2b8d514bea"),
    (C, "getdigits_long", "3816094261e53cf359e63a7ffece55ec7678cf4aadd9d21dd0f9e40f820047a4"),
    (C, "getdigits_int32", "078aadac890a8ee818c8a48835fe71a0af73d9d42f0ec9b728183ab6ad5fb63a"),
]
PRELUDE_EXTRA += r"""#include "vp_strtoimax.h"
#define SIZEOF_INT 4
#define SIZEOF_LONG 8
#define SIZEOF_INTMAX_T 8
// <assert.h> with asserts enabled: a failed assert aborts, and abort() must be unreachable.
#define assert(e) do { if (!(e)) { abort(); } } while (0)
"""
GHOST_PARAMS.update({
    "try_getdigits": ("bool try_getdigits(char **pp, intmax_t *nr)", "size_t n"),
    "getdigits": ("intmax_t getdigits(char **pp, bool strict, intmax_t def)", "size_t n"),
    "getdigits_int": ("int getdigits_int(char **pp, bool strict, int def)", "size_t n"),
    "getdigits_long": ("long getdigits_long(char **pp, bool strict, long def)", "size_t n"),
    "getdigits_int32": ("int32_t getdigits_int32(char **pp, bool strict, int32_t def)", "size_t n"),
})
LOOPS["try_getdigits"] = [("  errno = 0;", "ghost subj_exists(*pp, n);")]
LOGIC += r"""
/*@ ghost
  // a string has a strtoimax subject sequence: a first non-space byte and, after the
  // optional sign, a first non-digit (the NUL at s[n] is neither)
  /@ requires str_len(s, n);
     assigns \nothing;
     ensures \exists integer w, e; subj(s, w, e); @/
  void subj_exists(char *s, size_t n) {
    size_t w = 0;
    /@ loop invariant 0 <= w <= n && \forall integer k; 0 <= k < w ==> c_space(s[k]);
       loop assigns w; loop variant n - w; @/
    while (w < n && (s[w] == 32 || (s[w] >= 9 && s[w] <= 13))) w++;
    size_t e = w + ((s[w] == 43 || s[w] == 45) ? 1 : 0);
    /@ loop invariant sdigits(s, w) <= e <= n && \forall integer k; sdigits(s, w) <= k < e ==> 48 <= s[k] <= 57;
       loop assigns e; loop variant n - e; @/
    while (e < n && s[e] >= 48 && s[e] <= 57) e++;
    /@ assert subj(s, w, e); @/
  }
*/
"""
GHOST_ARGS.update({
    "try_getdigits": [("strtoimax(*pp, pp, 10)", "n")],
    "getdigits": [("try_getdigits(pp, &number)", "n")],
    "getdigits_int": [("getdigits(pp, strict, def)", "n")],
    "getdigits_long": [("getdigits(pp, strict, def)", "n")],
    "getdigits_int32": [("getdigits(pp, strict, def)", "n")],
})
_S = r"\at(*pp, Pre)"
_REQ = rf"""requires \valid(pp) && str_len(*pp, n) && \separated(pp, *pp + (0 .. n), &errno);"""
_ALL = rf"\forall integer w, e; subj{{Pre}}({_S}, w, e) ==> \let d = sdigits{{Pre}}({_S}, w); \let v = svalue{{Pre}}({_S}, w, e);"
_PTR = rf"""ensures \exists integer w, e; subj{{Pre}}({_S}, w, e);
    ensures {_ALL} *pp == (e == d ? {_S} : {_S} + e);"""


def _getd(lo, hi, extra=""):
    return rf"""{_REQ}
    requires strict != 0 ==> {_ALL} e > d ==> {lo} <= v <= {hi};   // strict and out of range: abort()
    assigns *pp, errno;
    {_PTR}
    ensures {_ALL} \result == (e == d ? 0 : ({lo} <= v <= {hi} ? v : def));"""


_IMIN, _IMAX = "-9223372036854775808", "9223372036854775807"
CONTRACTS.update({
    "try_getdigits": rf"""{_REQ}
    requires \valid(nr) && \separated(nr, pp, *pp + (0 .. n), &errno);
    assigns *pp, *nr, errno;
    {_PTR}
    ensures {_ALL} e == d ==> *nr == 0 && \result != 0 && errno == 0;
    ensures {_ALL} e > d ==> (\result != 0 <==> {_IMIN} <= v <= {_IMAX})
              && *nr == (v > {_IMAX} ? {_IMAX} : (v < {_IMIN} ? {_IMIN} : v))
              && errno == ({_IMIN} <= v <= {_IMAX} ? 0 : 34);""",
    "getdigits": _getd(_IMIN, _IMAX),
    "getdigits_int": _getd("-2147483648", "2147483647"),
    "getdigits_long": _getd(_IMIN, _IMAX),
    "getdigits_int32": _getd("-2147483648", "2147483647"),
})
