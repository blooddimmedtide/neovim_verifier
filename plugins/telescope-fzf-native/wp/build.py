"""Annotated standalone copy of fzf.c's small helpers for Frama-C WP.

Usage: python3 -I build.py <path/to/fzf.c> <out.c>
Copies the exact text of the header region (macros, slice types, enums) and of
each helper (sha256 pinned; trailing_whitespaces in its fixed form), puts an
ACSL contract before each helper and loop annotations before exact anchor
lines, all as comments. Removing the /*@ ... */ comments gives the original
text back (checked). <ctype.h> is replaced by stubs/fzf_ctype.h (C-locale
contracts); fzf.h is included from the source directory.
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from contracts import CONTRACTS, LOOPS, LOGIC
import contracts_match
CONTRACTS = {**CONTRACTS, **contracts_match.CONTRACTS}
LOOPS = {**LOOPS, **contracts_match.LOOPS}
LOGIC = LOGIC + contracts_match.LOGIC

# region start line, region end line (exact text), sha256 of the region
REGION = ("// TODO(conni2461): UNICODE HEADER", "} char_types;",
          "d3c4d55ba351ad934d8fb8ff880fef09d04794b1a4ddcf9ce0ca5925e241e59d")
SHA = {
    "index_byte": None, "leading_whitespaces": None, "trailing_whitespaces": None,
    "copy_runes": None, "copy_into_i16": None, "trim_whitespace_left": None,
    "max16": None, "min64u": None, "char_class_of_ascii": None, "char_class_of": None,
    "bonus_for": None, "bonus_at": None, "normalize_rune": None, "is_ascii": None,
    # positions and scoring (contracts_match.py)
    "resize_pos": None, "unsafe_append_pos": None, "append_pos": None, "insert_range": None,
    "calculate_score": None,
    "fzf_prefix_match": None, "fzf_suffix_match": None, "fzf_equal_match": None,
}
PINS = os.path.join(HERE, "pins.txt")   # name sha256, reviewed
PRELUDE = """\
// Prelude: fzf.c's includes, with <ctype.h> replaced by C-locale contracts.
#include "fzf.h"
#include <string.h>
#include <stdlib.h>
#include "fzf_ctype.h"
#include "fzf_realloc.h"   // realloc as C11 7.22.3.5 describes it, on uint32_t arrays
"""
INCLUDES = ['#include "fzf.h"', "#include <string.h>", "#include <ctype.h>", "#include <stdlib.h>"]


def find(lines, name):
    pat = re.compile(r"^[A-Za-z_][\w \*]*\b" + re.escape(name) + r"\(")
    starts = [i for i, l in enumerate(lines) if pat.match(l)]
    if len(starts) != 1:
        sys.exit(f"build: {name}: expected one definition, found {len(starts)}")
    e = starts[0]
    while not lines[e].startswith("}"):
        e += 1
    return starts[0], e


def main(src, out, show=False):
    lines = open(src).read().split("\n")
    pins = dict(l.split() for l in open(PINS) if l.strip() and not l.startswith("#"))
    for inc in INCLUDES:
        if inc not in lines:
            sys.exit(f"build: {src} no longer has {inc}")
    s = lines.index(REGION[0]); e = lines.index(REGION[1])
    region = "\n".join(lines[s:e + 1])
    h = hashlib.sha256(region.encode()).hexdigest()
    if show: print("REGION", h)
    elif h != REGION[2] and not os.environ.get("FZF_WP_MUTANT"):
        sys.exit(f"build: header region changed: {h}")
    parts = [PRELUDE, f"// {os.path.basename(src)}:{s + 1} (verbatim)\n{region}\n", LOGIC]
    for name in SHA:
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if show:
            print(name, h); continue
        if pins.get(name) != h and not os.environ.get("FZF_WP_MUTANT"):   # run_mutants.py only
            sys.exit(f"build: {name} ({src}:{s + 1}) differs from the reviewed text: sha256 {h}")
        ann = piece
        for anchor, annot in LOOPS.get(name, []):
            if ann.count(anchor) != 1:
                sys.exit(f"build: {name}: anchor not found once: {anchor!r}")
            indent = re.match(r"\s*", anchor).group(0)
            ann = ann.replace(anchor, f"{indent}/*@ {annot} */\n{anchor}")
        assert re.sub(r"[ \t]*/\*@.*?\*/\n", "", ann, flags=re.S) == piece, name
        parts.append(f"// {os.path.basename(src)}:{s + 1} (verbatim, plus ACSL comments)\n/*@ {CONTRACTS[name]} */\n{ann}\n")
    if not show:
        open(out, "w").write("\n".join(parts))


if __name__ == "__main__":
    if sys.argv[1] == "--show":
        main(sys.argv[2], None, True)
    else:
        main(sys.argv[1], sys.argv[2])
