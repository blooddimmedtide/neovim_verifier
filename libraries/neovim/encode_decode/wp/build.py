"""Annotated standalone copy of encode.c / decode.c functions for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c>
       python3 -I build.py --pin <neovim checkout>     (print sha256 of each piece)
Each function is the exact upstream text (sha256 pinned, via tools/extract_c.py).
Contracts sit on prototypes in the prelude (Frama-C joins them to the definition);
loop annotations are inserted as /*@ */ comments, and the build checks that
removing every /*@ ... */ gives back the pinned text exactly.
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import PRELUDE, CHECKS, LOOPS

EN = "src/nvim/eval/encode.c"
DE = "src/nvim/eval/decode.c"
PIECES = [  # upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
    (EN, "encode_blob_write", "PIN"),
    (DE, "typval_parser_error_free", "PIN"),
]
SHA = {}
exec(open(os.path.join(HERE, "pins.txt")).read())


def strip(t):
    t = re.sub(r"^[ \t]*/\*@.*?\*/\n", "", t, flags=re.S | re.M)   # whole-line annotations
    return re.sub(r" /\*@.*?\*/", "", t, flags=re.S)                 # inline ghost arguments


def main():
    if sys.argv[1] == "--pin":
        tree = sys.argv[2]
        for path, name, _ in PIECES:
            lines = open(f"{tree}/{path}").read().split("\n")
            s, e = find(lines, name)
            print(f'SHA["{name}"] = "{hashlib.sha256(chr(10).join(lines[s:e + 1]).encode()).hexdigest()}"')
        return
    tree, out = sys.argv[1], sys.argv[2]
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    parts = [PRELUDE]
    for path, name, _ in PIECES:
        lines = open(f"{tree}/{path}").read().split("\n")
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if SHA.get(name) != h:
            sys.exit(f"build: {name} ({path}:{s + 1}) differs from the pinned text: {h}")
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
