"""Verbatim u_clearline / u_update_named_mark (src/nvim/undo.c), sha256 pinned, after model_misc.h.

Usage: python3 -I build_misc.py <neovim checkout> <out.c>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build

PINS = {"u_clearline": "fdcda8c2a279ef41984d1688e8053cf12b036cda5da421cca35a5cb179e27ea9", "u_update_named_mark": "0acded18d5b8d5b879669247589e238bcc3c58aba5aeedf4514eef6555ae8c6e"}

def main():
    tree, out = sys.argv[1], sys.argv[2]
    parts = ['#include "model_misc.h"']
    for name, want in PINS.items():
        where, text, h = build.piece(tree, "src/nvim/undo.c", name)
        if os.environ.get("PRINT_HASHES"): print(name, h); continue
        if h != want: sys.exit(f"build_misc: {name} ({where}) changed: sha256 {h}")
        parts.append(f"// {where} (verbatim)\n{text}\n")
    open(out, "w").write("\n".join(parts) + "\n")

if __name__ == "__main__":
    main()
