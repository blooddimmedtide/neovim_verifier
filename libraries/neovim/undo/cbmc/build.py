"""Write a standalone C file holding exact upstream text from src/nvim/undo.c and src/nvim/fileio.c.

Usage: python3 -I build.py <neovim checkout> <out.c> [--print-hashes]
Each piece (signature to the closing "}" in column 0) is copied verbatim and checked against the
sha256 recorded below, so a changed upstream file cannot be proved by accident. A piece whose hash
matches FIXED is the fixed version from blooddimmedtide/verified_neovim and defines a macro.
The prelude (model.h) supplies the types and a byte-array model of FILE.
"""
import hashlib, os, re, sys

PIECES = [  # (file, function)
    ("src/nvim/fileio.c", "get2c"), ("src/nvim/fileio.c", "get4c"), ("src/nvim/fileio.c", "get8ctime"),
    ("src/nvim/undo.c", "undo_write"), ("src/nvim/undo.c", "undo_write_bytes"),
    ("src/nvim/undo.c", "put_header_ptr"), ("src/nvim/undo.c", "undo_read_4c"),
    ("src/nvim/undo.c", "undo_read_len"), ("src/nvim/undo.c", "undo_read_2c"),
    ("src/nvim/undo.c", "undo_read_byte"), ("src/nvim/undo.c", "undo_read_time"),
    ("src/nvim/undo.c", "undo_read"), ("src/nvim/undo.c", "undo_read_string"),
    ("src/nvim/undo.c", "serialize_pos"), ("src/nvim/undo.c", "unserialize_pos"),
    ("src/nvim/undo.c", "serialize_visualinfo"), ("src/nvim/undo.c", "unserialize_visualinfo"),
    ("src/nvim/undo.c", "uhp_seq_cmp"), ("src/nvim/undo.c", "uhp_table_find"),
]
REVIEWED = {}   # filled from hashes.txt
FIXED = {}      # name -> (sha256, macro)

def load():
    here = os.path.dirname(os.path.abspath(__file__))
    for line in open(os.path.join(here, "hashes.txt")):
        f = line.split()
        if len(f) == 2: REVIEWED[f[0]] = f[1]
        elif len(f) == 4 and f[0] == "fixed": FIXED[f[1]] = (f[2], f[3])
    return here

def piece(tree, path, name):
    lines = open(os.path.join(tree, path)).read().split("\n")
    sp = re.compile(r"^[A-Za-z_][\w \*]*\b" + re.escape(name) + r"\(")
    starts = [i for i, l in enumerate(lines) if sp.match(l) and not l.rstrip().endswith(";")]
    if len(starts) != 1: sys.exit(f"build: {name}: {len(starts)} definitions in {path}")
    s = starts[0]
    # keep the doc comment out; take signature .. first "}" in column 0
    e = next(i for i in range(s, len(lines)) if lines[i] == "}")
    text = "\n".join(lines[s:e + 1])
    return f"{path}:{s + 1}", text, hashlib.sha256(text.encode()).hexdigest()

def main():
    here = load()
    tree, out = sys.argv[1], sys.argv[2]
    parts = ['#include "model.h"']
    bad = False
    for path, name in PIECES:
        where, text, h = piece(tree, path, name)
        if "--print-hashes" in sys.argv: print(name, h); continue
        if name in FIXED and h == FIXED[name][0]:
            parts.append(f"#define {FIXED[name][1]} 1  // fixed fork version")
        elif REVIEWED.get(name) != h:
            print(f"build: {name} ({where}) changed: sha256 {h}", file=sys.stderr); bad = True
        parts.append(f"// {where} (verbatim)\n{text}\n")
    if "--print-hashes" in sys.argv: return
    if bad: sys.exit(1)
    open(out, "w").write("\n".join(parts) + "\n")

if __name__ == "__main__":
    main()
