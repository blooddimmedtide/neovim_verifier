"""Verbatim undo_allowed, corruption_error (src/nvim/undo.c) and expr_map_locked
(src/nvim/ex_docmd.c), sha256 pinned, after model_allow.h.

Usage: python3 -I build_allow.py <neovim checkout> <out.c>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build

PINS = {("src/nvim/ex_docmd.c", "expr_map_locked"): "3c4a6e34eafe2ba146d7960e9f7e2c723ab8d219e9479e364189409e11391faa", ("src/nvim/undo.c", "undo_allowed"): "9d2f83beca9d3f946a4cfde29fce0cdaf721d3c3758b8c599d8d25793ab2d52e",
        ("src/nvim/undo.c", "corruption_error"): "135c927df26868243274365fe75c8e85143c77f9396573033830acc456e48489"}

def main():
    tree, out = sys.argv[1], sys.argv[2]
    parts = ['#include "model_allow.h"']
    for (path, name), want in PINS.items():
        where, text, h = build.piece(tree, path, name)
        if os.environ.get("PRINT_HASHES"): print(name, h); continue
        if h != want: sys.exit(f"build_allow: {name} ({where}) changed: sha256 {h}")
        parts.append(f"// {where} (verbatim)\n{text}\n")
    open(out, "w").write("\n".join(parts) + "\n")

if __name__ == "__main__":
    main()
