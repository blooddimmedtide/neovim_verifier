"""Verbatim u_update_save_nr (src/nvim/undo.c), sha256 pinned, after model_save.h.

Usage: python3 -I build_save.py <neovim checkout> <out.c>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build

PINS = {"u_update_save_nr": "f0976bf901f6356ee52f253be58e507a32a417ad39f19c8676da6f744d77c22b"}

def main():
    tree, out = sys.argv[1], sys.argv[2]
    parts = ['#include "model_save.h"']
    for name, want in PINS.items():
        where, text, h = build.piece(tree, "src/nvim/undo.c", name)
        if os.environ.get("PRINT_HASHES"): print(name, h); continue
        if h != want: sys.exit(f"build_save: {name} ({where}) changed: sha256 {h}")
        parts.append(f"// {where} (verbatim)\n{text}\n")
    open(out, "w").write("\n".join(parts) + "\n")

if __name__ == "__main__":
    main()
