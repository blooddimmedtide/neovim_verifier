"""Annotated standalone copy of typval.c list functions for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c>
       python3 -I build.py --pin <neovim checkout>     (print sha256 of each piece)
Each function is the exact upstream text (sha256 pinned, via tools/extract_c.py).
One mechanical step: TV_LIST_ITER_CONST / TV_LIST_ITER_MOD invocations are expanded
from typval.h's own macro text (pinned too), as cpp would, so a loop invariant can be
attached. Contracts sit on prototypes in the prelude; loop annotations and ghost code are
inserted as /*@ */ comments, and the build checks that removing every /*@ ... */ gives
back the (expanded) pinned text exactly.
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import PRELUDE, CHECKS, LOOPS

TV = "src/nvim/eval/typval.c"
TH = "src/nvim/eval/typval.h"
PIECES = [  # upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
    (TH, "tv_list_len"),
    (TH, "tv_list_uidx"),
    (TV, "tv_list_reverse"),
    (TV, "tv_list_find"),
    (TV, "tv_list_idx_of_item"),
    (TV, "tv_list_find_index"),
    (TV, "tv_list_check_range_index_one"),
    (TV, "tv_list_check_range_index_two"),
]
SHA = {}
exec(open(os.path.join(HERE, "pins.txt")).read())
MACRO_SHA = "MACRO_PIN"
exec(open(os.path.join(HERE, "pins_macro.txt")).read())


def strip(t):
    return re.sub(r"[ \t]*/\*@.*?\*/\n?", "", t, flags=re.S)


def macro_text(tree):
    t = open(f"{tree}/{TH}").read()
    m = re.search(r"^#define TV_LIST_ITER_MOD\(modifier, l, li, code\) \\\n((?:.*\\\n)*.*)$", t, re.M)
    m2 = re.search(r"^#define TV_LIST_ITER_CONST\(l, li, code\) \\\n(.*)$", t, re.M)
    if not m or not m2:
        sys.exit("build: TV_LIST_ITER macros not found")
    return m.group(0) + "\n" + m2.group(0), m.group(1), m2.group(1).strip()


def split_args(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "," and depth == 0:
            out.append(cur.strip()); cur = ""; continue
        depth += ch in "([{"; depth -= ch in ")]}"
        cur += ch
    out.append(cur.strip())
    return out


def expand_iter(piece, body):
    """Expand `TV_LIST_ITER_CONST(l, li, {code});` using TV_LIST_ITER_MOD's body."""
    body = re.sub(r"\s*\\\n\s*", " ", body).strip()
    while "TV_LIST_ITER_CONST(" in piece:
        s = piece.index("TV_LIST_ITER_CONST(")
        i, depth = s + len("TV_LIST_ITER_CONST("), 1
        while depth:
            depth += piece[i] in "([{"; depth -= piece[i] in ")]}"; i += 1
        args = split_args(piece[s + len("TV_LIST_ITER_CONST("):i - 1])
        sub = dict(zip(["modifier", "l", "li", "code"], ["const"] + args))
        exp = re.sub(r"\b(modifier|l|li|code)\b", lambda m: sub[m.group(1)], body)
        piece = piece[:s] + exp + piece[i:]
    return piece


def main():
    if sys.argv[1] == "--pin":
        tree = sys.argv[2]
        for path, name in PIECES:
            lines = open(f"{tree}/{path}").read().split("\n")
            s, e = find(lines, name)
            print(f'SHA["{name}"] = "{hashlib.sha256(chr(10).join(lines[s:e + 1]).encode()).hexdigest()}"')
        print(f'#MACRO_SHA = "{hashlib.sha256(macro_text(tree)[0].encode()).hexdigest()}"', file=sys.stderr)
        return
    tree, out = sys.argv[1], sys.argv[2]
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    mt, mbody, cbody = macro_text(tree)
    if hashlib.sha256(mt.encode()).hexdigest() != MACRO_SHA:
        sys.exit("build: TV_LIST_ITER macros differ from the pinned text")
    if cbody != "TV_LIST_ITER_MOD(const, l, li, code)":
        sys.exit("build: TV_LIST_ITER_CONST changed")
    parts = [PRELUDE]
    for path, name in PIECES:
        lines = open(f"{tree}/{path}").read().split("\n")
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if SHA.get(name) != h:
            sys.exit(f"build: {name} ({path}:{s + 1}) differs from the pinned text: {h}")
        piece = expand_iter(piece, mbody)
        ann = piece
        for anchor, text in LOOPS.get(name, []):
            if ann.count(anchor) != 1:
                sys.exit(f"build: anchor for {name} not unique: {anchor!r}")
            ann = ann.replace(anchor, text + anchor)
        if strip(ann) != piece:
            sys.exit(f"build: {name}: annotations changed the code")
        parts.append(f"// {path}:{s + 1} (verbatim, sha256 {h})\n{ann}\n")
    open(out, "w").write("\n".join(parts))


main()
