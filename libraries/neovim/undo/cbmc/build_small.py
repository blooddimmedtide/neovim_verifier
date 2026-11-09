"""Verbatim get_undolevel / zero_fmark_additional_data (src/nvim/undo.c), sha256 pinned, after model_small.h.

Usage: python3 -I build_small.py <neovim checkout> <out.c>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build

PINS = {"get_undolevel": "58402e58236d761ac6360b2ed7f3b9ba5578e039dde0514ed328d8fded55f74b", "zero_fmark_additional_data": "c92fd77b8b7f17afa92456e985a892a972ce1a975158514cb501cba42c854cb6"}

def main():
    tree, out = sys.argv[1], sys.argv[2]
    parts = ['#include "model_small.h"']
    for name, want in PINS.items():
        where, text, h = build.piece(tree, "src/nvim/undo.c", name)
        if os.environ.get("PRINT_HASHES"): print(name, h); continue
        if h != want: sys.exit(f"build_small: {name} ({where}) changed: sha256 {h}")
        parts.append(f"// {where} (verbatim)\n{text}\n")
    open(out, "w").write("\n".join(parts) + "\n")

if __name__ == "__main__":
    main()
