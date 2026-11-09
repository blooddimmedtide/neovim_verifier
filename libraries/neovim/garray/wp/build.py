"""Annotated standalone copy of garray.c for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c> [upstream|fixed] [function]
Each function is the exact upstream (or fixed-fork) text, sha256 pinned. The build
  1. expands the two garray.h macros the file uses (GA_DEEP_CLEAR_PTR, GA_APPEND)
     mechanically from the header's own text (the header text is pinned too);
  2. applies the one declared tool patch (tool_patches.py: GA_APPEND's uint8_t
     store becomes the identical char store, proved equal in ../equiv/);
  3. inserts ACSL as comments only, and checks that removing every /*@ ... */
     gives back the text of step 2 exactly.
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import LOGIC, contracts, annotations
from tool_patches import PATCHES

F = "src/nvim/garray.c"
H = "src/nvim/garray.h"
SHA = {  # upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
    "ga_clear": "49c1905661a55b9d902a7d5f52ef0467a0da4f0f7d9329034a0aea4e2282eb45",
    "ga_clear_strings": "188ea189d9ef2d357ebc782ff7c33824202bab3e584f644b10a1a1220323c3b0",
    "ga_init": "5640844fbb06dc9a04eac1b0e1889082d824cf03391686d85a795311b02286f7",
    "ga_set_growsize": "d1a563f10d1952a66d705dd9cc14119ba34a6882f911654f0419242a4a932710",
    "ga_grow": "20d957f4f5069b6c638e0cd580803ca5b0d4b4edb9a2cb1b3560cd7f57bb6bfd",
    "ga_remove_duplicate_strings": "ea1777a6d527bf7f5bb5fca2897e92eb50b3942a427fe63d6a29596d3c0599af",
    "ga_concat_strings": "df17386029f7bf582c1aecfea62f310c642f49277b0202f16e29497d63257f22",
    "ga_concat": "78a938f2433e5aef31b259356f7a92540faa70392095b4e162422a8d4862e29e",
    "ga_concat_len": "d6cb297f246625bc317a14c55672d04c0dfb30e281559d28ac56d7cc482ca3ae",
    "ga_append": "a7ca54b2d4b10ffe0c8eb4494b9b55deca38f5518d0e9ba75bd6e2f9d5f6d40c",
    "ga_append_via_ptr": "c0aa2a123cf32f8eba52144220a09065b29441cb5a1a03a3b7e1ac26090ad496",
}
FIXED_SHA = {  # verified_neovim, fix commits 850a906 (ga_grow) and dec9b23 (ga_concat_strings)
    "ga_grow": "1308ffd2c9299892f3594c553502053d2cb9b8ad7ee200a0779a034ddf749b27",
    "ga_concat_strings": "c50386fec69d50563b8b4ea972bdea29c0c592b922ad45d0a2e4cc1ec3468b79",
}
MACROS_SHA = {  # garray.h at the pinned commit (python3 -I build.py --pin <tree>)
    "GA_APPEND": "5d0fd2e8a290d55a7c7029ec7f6dd09e44d5e532dc9a7809a01472c7dbad761c",
    "GA_DEEP_CLEAR": "d687a89a35619fd70f33e974d76ae1d4ee603dee91f1ed43454545535ab26f2f",
    "GA_DEEP_CLEAR_PTR": "4df0791fd945f99df19d89e958e9960ed4222b586877eeef3213c0abcc350448",
}
PRELUDE = """\
// Prelude: garray.c's system headers (<string.h> replaced by vp_string.h), the
// garray_T type and the macros it uses as Neovim defines them (each checked
// against the upstream text by build.py), and stubs for what it calls.
#include <limits.h>
#include <stdbool.h>
#include <stdint.h>
#include "vp_garray.h"
#define NUL '\\000'
#define MIN(X, Y) ((X) < (Y) ? (X) : (Y))
#define MAX(X, Y) ((X) > (Y) ? (X) : (Y))
#define WLOG(...) vp_wlog()
#define _(x) ((char *)(x))
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_NONNULL_RET
#define FREE_PTR_PTR(ptr) xfree(*(ptr))
typedef struct {
  int ga_len;                       // current number of items used
  int ga_maxlen;                    // maximum number of items possible
  int ga_itemsize;                  // sizeof(item)
  int ga_growsize;                  // number of items to grow each time
  void *ga_data;                    // pointer to the first item
} garray_T;
extern const char e_resulting_text_too_long[];
void ga_grow(garray_T *gap, int n) /*@ ghost (char *a1) */;
void ga_clear(garray_T *gap);
void ga_set_growsize(garray_T *gap, int growsize);
void ga_concat_len(garray_T *const gap, const char *restrict s, const size_t len);
"""
CHECKS = [("src/nvim/macros_defs.h", "# define MIN(X, Y) ((X) < (Y) ? (X) : (Y))"),
          ("src/nvim/macros_defs.h", "# define MAX(X, Y) ((X) > (Y) ? (X) : (Y))"),
          ("src/nvim/ascii_defs.h", "#define NUL             '\\000'"),
          ("src/nvim/log.h", "#define WLOG(...) logmsg(LOGLVL_WRN, NULL, __func__, __LINE__, true, __VA_ARGS__)"),
          ("src/nvim/gettext_defs.h", "# define _(x) ((char *)(x))  // NOLINT(bugprone-reserved-identifier)"),
          (H, "#define FREE_PTR_PTR(ptr) xfree(*(ptr))"),
          ("src/nvim/path.h", "  kPathCmpLiteral = 1 << 0,  ///< Compare paths literally."),
          ("src/nvim/path.h", "  kPathCmpExpand  = 1 << 1,  ///< Expand env vars in the first path."),
          ("src/nvim/path.h", "  kPathCmpFull    = 1 << 2,  ///< Compare full names when FileIds are unavailable."),
          ("src/nvim/option_vars.h", "EXTERN int p_fic;               ///< 'fileignorecase'"),
          ("src/nvim/errors.h",
           'EXTERN const char e_resulting_text_too_long[] INIT(= N_("E1240: Resulting text too long"));')]
# garray_T, verbatim
TYPE = """typedef struct {
  int ga_len;                       // current number of items used
  int ga_maxlen;                    // maximum number of items possible
  int ga_itemsize;                  // sizeof(item)
  int ga_growsize;                  // number of items to grow each time
  void *ga_data;                    // pointer to the first item
} garray_T;"""


def macro(htext, name):
    """(params, body) of `#define name(params) body`, joined over backslash-newlines."""
    m = re.search(r"^#define " + name + r"\(([^)]*)\) ((?:.*\\\n)*.*)$", htext, re.M)
    if not m:
        sys.exit(f"build: macro {name} not found in {H}")
    params = [p.strip() for p in m.group(1).split(",")]
    body = re.sub(r"\s*\\\n\s*", " ", m.group(2)).strip()
    return params, body, m.group(0)


def split_args(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "," and depth == 0:
            out.append(cur.strip()); cur = ""
            continue
        depth += ch in "([{"
        depth -= ch in ")]}"
        cur += ch
    out.append(cur.strip())
    return out


def expand(text, name, params, body):
    """Replace each `name(args)` in text by body with the params substituted (as cpp does)."""
    while True:
        m = re.search(r"\b" + name + r"\(", text)
        if not m:
            return text
        i, depth = m.end(), 1
        while depth:
            depth += text[i] == "("
            depth -= text[i] == ")"
            i += 1
        args = split_args(text[m.end():i - 1])
        assert len(args) == len(params), (name, args)
        out = re.sub(r"\b(" + "|".join(map(re.escape, params)) + r")\b",
                     lambda mm: args[params.index(mm.group(1))], body)
        text = text[:m.start()] + out + text[i:]


def strip(s):
    s = re.sub(r"^[ \t]*/\*@.*?\*/\n", "", s, flags=re.S | re.M)
    s = re.sub(r" /\*@.*?\*/", "", s, flags=re.S)
    return re.sub(r"/\*@.*?\*/ ", "", s, flags=re.S)


def main(tree, out, mode="upstream", only=None):
    fixed = mode == "fixed"
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    if TYPE not in open(f"{tree}/src/nvim/garray_defs.h").read():
        sys.exit("build: garray_T changed in garray_defs.h")
    htext = open(f"{tree}/{H}").read()
    macros = {}
    for name, want in MACROS_SHA.items():
        params, body, raw = macro(htext, name)
        h = hashlib.sha256(raw.encode()).hexdigest()
        if h != want:
            sys.exit(f"build: macro {name} changed in {H}: sha256 {h}")
        macros[name] = (params, body)
    lines = open(f"{tree}/{F}").read().split("\n")
    C, A = contracts(fixed), annotations(fixed)
    parts, missing = [PRELUDE, LOGIC], False
    for name, want in SHA.items():
        if only and name != only:
            continue
        if name not in C:
            print(f"build: {name}: no contract yet, left out (the run fails)", file=sys.stderr)
            missing = True
            continue
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if fixed and name in FIXED_SHA:
            want = FIXED_SHA[name]
        if h != want:
            sys.exit(f"build: {name} ({F}:{s + 1}) differs from the pinned {mode} text: sha256 {h}")
        code = piece
        for mname in ("GA_DEEP_CLEAR_PTR", "GA_DEEP_CLEAR", "GA_APPEND"):
            code = expand(code, mname, *macros[mname])
        for old, new in PATCHES.get(name, []):
            if code.count(old) != 1:
                sys.exit(f"build: {name}: tool patch anchor not found once: {old!r}")
            code = code.replace(old, new)
        annotated = code
        for kind, anchor, annot in A.get(name, []):
            if annotated.count(anchor) != 1:
                sys.exit(f"build: {name}: anchor not found once: {anchor!r}")
            if kind == "before":    # a whole line before the anchor line
                indent = re.match(r"\s*", anchor).group(0)
                annotated = annotated.replace(anchor, f"{indent}/*@ {annot} */\n{anchor}")
            elif kind == "after":   # inline, right after the anchor text
                annotated = annotated.replace(anchor, f"{anchor} /*@ {annot} */")
            elif kind == "inline":  # inline, right before the anchor text
                annotated = annotated.replace(anchor, f"/*@ {annot} */ {anchor}")
            else:
                sys.exit(f"build: bad annotation kind {kind}")
        if strip(annotated) != code:
            sys.exit(f"build: {name}: stripping the annotations does not give the source back")
        parts.append(f"// {F}:{s + 1} ({mode}, verbatim plus ACSL comments"
                     f"{', macros expanded' if code != piece else ''})\n/*@ {C[name]} */\n{annotated}\n")
    open(out, "w").write("\n".join(parts))
    if missing:
        sys.exit(2)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--pin":
        htext = open(f"{sys.argv[2]}/{H}").read()
        for n in ("GA_APPEND", "GA_DEEP_CLEAR", "GA_DEEP_CLEAR_PTR"):
            print(n, hashlib.sha256(macro(htext, n)[2].encode()).hexdigest())
        sys.exit(0)
    main(*sys.argv[1:])
