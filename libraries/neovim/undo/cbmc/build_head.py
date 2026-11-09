"""Verbatim u_get_headentry / u_getbot (src/nvim/undo.c), sha256 pinned, after model_head.h.

Usage: python3 -I build_head.py <neovim checkout> <out.c>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build

PINS = {"u_get_headentry": "96311cb1ce2c6bf82ac58b38158e1057a5fa88ad408fb1ab8d2f63a075eb3dcf", "u_getbot": "67514957a680ba22de386bd55898515b0b10edafa402fd43a4efb4132329dc67"}

def main():
    tree, out = sys.argv[1], sys.argv[2]
    parts = ['#include "model_head.h"']
    for name, want in PINS.items():
        where, text, h = build.piece(tree, "src/nvim/undo.c", name)
        if os.environ.get("PRINT_HASHES"): print(name, h); continue
        if h != want: sys.exit(f"build_head: {name} ({where}) changed: sha256 {h}")
        parts.append(f"// {where} (verbatim)\n{text}\n")
    open(out, "w").write("\n".join(parts) + "\n")

if __name__ == "__main__":
    main()
