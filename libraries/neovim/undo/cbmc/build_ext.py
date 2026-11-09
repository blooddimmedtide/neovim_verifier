"""Like build.py, plus serialize_extmark / unserialize_extmark (verbatim, sha256 pinned below), for harness_ext.c.

Usage: python3 -I build_ext.py <neovim checkout> <out.c>
"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build

EXTRA = {
    "serialize_extmark": "d9075759b5632bfd787e9cf6283d7aa104a4a3b181bbbb7385f50de1613dc676",
    "unserialize_extmark": "5a5393b251d73e19b26eeb45e03cc0afa1ffd5a80ada81c40a1ef8fe7271e9ca",
}

def main():
    tree, out = sys.argv[1], sys.argv[2]
    sys.argv = [sys.argv[0], tree, out]
    build.main()
    parts = [open(out).read(), "#include \"model_ext.h\""]
    for name, want in EXTRA.items():
        where, text, h = build.piece(tree, "src/nvim/undo.c", name)
        if os.environ.get("PRINT_HASHES"): print(name, h); continue
        if h != want: sys.exit(f"build_ext: {name} ({where}) changed: sha256 {h}")
        parts.append(f"// {where} (verbatim)\n{text}\n")
    open(out, "w").write("\n".join(parts))

if __name__ == "__main__":
    main()
