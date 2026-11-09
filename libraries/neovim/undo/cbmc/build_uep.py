"""Like build.py, plus serialize_uep / unserialize_uep (verbatim, sha256 pinned below), for harness_uep.c.

Usage: python3 -I build_uep.py <neovim checkout> <out.c>
"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build

EXTRA = {
    "serialize_uep": "98e18eb41e661cbf3b3fb198f7c968a732bc8277c441f44aeb90a3661a811ce9",
    "unserialize_uep": "b644d889e09ddc979706732d8b772a8579d41879c316ba18fc69969d5e37fa92",
}

def main():
    tree, out = sys.argv[1], sys.argv[2]
    sys.argv = [sys.argv[0], tree, out]
    build.main()
    parts = [open(out).read(), "#include \"model_uep.h\""]
    for name, want in EXTRA.items():
        where, text, h = build.piece(tree, "src/nvim/undo.c", name)
        if os.environ.get("PRINT_HASHES"): print(name, h); continue
        if h != want: sys.exit(f"build_uep: {name} ({where}) changed: sha256 {h}")
        parts.append(f"// {where} (verbatim)\n{text}\n")
    open(out, "w").write("\n".join(parts))

if __name__ == "__main__":
    main()
