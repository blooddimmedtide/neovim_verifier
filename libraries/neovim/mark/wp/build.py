"""Annotated standalone copy of mark.c functions for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c>
Each function is the exact pinned text (sha256). ACSL goes in comments only; removing every
/*@ ... */ gives the pinned text back. Each line of stubs/vp_mark.h that copies a Neovim
declaration must occur in the pinned headers (EXEMPT lines are explained in the prelude).
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import LOGIC, contracts, annotations

F = "src/nvim/mark.c"
PIECES = [  # sha256 at upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
    ("mark_view_make", "ca1f2df190b2ed4a8daceb6f1d465de51bd6ceac85197fa0990f2f69a0984b65"),
    ("mark_check_line_bounds", "244396d7a7a6a123de27c0538eb35c3707adbc77d011ca6fdc94cb1295bdae4e"),
    ("next_buffer_mark", "b00619ac2d2eb3c8f2c2f1bc5816474fdf58ae63c376456521549ed33f2e2502"),
    ("mark_jumplist_iter", "d7af75e9c720407826e1ec549fd49e65ac0e9d14c5c6673ce4c9ac3dbfc6feb3"),
    ("mark_global_iter", "547c98d56f15afb4cb7a6c40153b0bf69901654dfc1d34019c55d2f3d33d90bf"),
]
HEADERS = ["src/nvim/pos_defs.h", "src/nvim/mark_defs.h", "src/nvim/os/time_defs.h", "src/nvim/types_defs.h",
           "src/nvim/buffer_defs.h", "src/nvim/memline_defs.h", "src/nvim/ascii_defs.h", "src/nvim/gettext_defs.h"]
EXEMPT = ("#include", "//", "typedef struct {", "} ", "#define MAXLNUM", "#define ARRAY_SIZE", "#define FUNC_ATTR",
          "extern const char e_markinval", "xfmark_T namedfm", "typedef struct AdditionalData")
EXTRA = [("src/nvim/pos_defs.h", "enum { MAXLNUM = 0x7fffffff, };  ///< Maximal (invalid) line number"),
         ("src/nvim/macros_defs.h", "#define ARRAY_SIZE(arr) \\"),
         ("src/nvim/mark.h", "EXTERN xfmark_T namedfm[NGLOBALMARKS] INIT( = { 0 });"),
         ("src/nvim/errors.h", 'EXTERN const char e_markinval[] INIT(= N_("E19: Mark has invalid line number"));')]


def no_comment_tokens(where, text):
    """ACSL must not contain comment tokens: an annotation holding `*/ code /*@` would smuggle
    code past the strip check (review finding 1)."""
    body = text
    if "/*" in body or "*/" in body:
        sys.exit(f"build: {where}: annotation text contains a comment token")


def strip(s):
    s = re.sub(r"^[ \t]*/\*@.*?\*/\n", "", s, flags=re.S | re.M)
    s = re.sub(r" /\*@.*?\*/", "", s, flags=re.S)
    return re.sub(r"/\*@.*?\*/ ", "", s, flags=re.S)


def main(tree, out):
    lines = set()
    for h in HEADERS:
        lines |= set(open(f"{tree}/{h}").read().split("\n"))
    for l in open(f"{HERE}/stubs/vp_mark.h").read().split("\n"):
        if l.strip() and not l.startswith(EXEMPT) and l not in lines:
            sys.exit(f"build: prelude line not in the pinned headers: {l!r}")
    for path, text in EXTRA:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    C, A = contracts(), annotations()
    src = open(f"{tree}/{F}").read().split("\n")
    no_comment_tokens("LOGIC", LOGIC.strip()[3:-2])  # inside its own /*@ ... */
    parts = ['#include "vp_mark.h"', LOGIC]
    for name, want in PIECES:
        s, e = find(src, name)
        piece = "\n".join(src[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if h != want:
            sys.exit(f"build: {name} ({F}:{s + 1}) differs from the pinned text: sha256 {h}")
        no_comment_tokens(name + " contract", C[name])
        ann = piece
        for anchor, annot in A.get(name, []):
            if ann.count(anchor) != 1:
                sys.exit(f"build: {name}: anchor not found once: {anchor!r}")
            no_comment_tokens(name + " annotation", annot)
            indent = re.match(r"\s*", anchor).group(0)
            ann = ann.replace(anchor, f"{indent}/*@ {annot} */\n{anchor}")
        if strip(ann) != piece:
            sys.exit(f"build: {name}: stripping the annotations does not give the source back")
        # the contract goes before the function's first line
        parts.append(f"// {F}:{s + 1} (verbatim plus ACSL comments)\n/*@ {C[name]} */\n{ann}\n")
    open(out, "w").write("\n".join(parts))


if __name__ == "__main__":
    main(*sys.argv[1:])
