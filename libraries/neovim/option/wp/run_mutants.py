"""Planted-bug check: each mutant in ../mutants.toml must make the WP proof fail.

Usage: python3 -I run_mutants.py <neovim checkout> [timeout] [mutant id...]
A mutant is {id, function, file, old, new}: `old` must occur exactly once inside the
function's text; the build's sha pin is skipped (VP_MUTANT=1) for the mutated copy only.
Exit 0 = every mutant caught.
"""
import os, shutil, subprocess, sys, tempfile, tomllib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
FILES = ["src/nvim/option.c", "src/nvim/optionstr.c", "src/nvim/ascii_defs.h", "src/nvim/memory.h",
         "src/nvim/option_defs.h", "src/nvim/macros_defs.h", "src/nvim/types_defs.h"]


def main():
    tree, t = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "20")
    only = set(sys.argv[3:])
    ms = tomllib.load(open(os.path.join(HERE, "..", "mutants.toml"), "rb"))["mutant"]
    bad = []
    for m in ms:
        if only and m["id"] not in only:
            continue
        d = tempfile.mkdtemp()
        for f in FILES:
            os.makedirs(os.path.dirname(f"{d}/{f}"), exist_ok=True)
            shutil.copy(f"{tree}/{f}", f"{d}/{f}")
        lines = open(f"{d}/{m['file']}").read().split("\n")
        s, e = find(lines, m["function"])
        body = "\n".join(lines[s:e + 1])
        if body.count(m["old"]) != 1:
            sys.exit(f"{m['id']}: `old` occurs {body.count(m['old'])} times in {m['function']}")
        lines[s:e + 1] = body.replace(m["old"], m["new"]).split("\n")
        open(f"{d}/{m['file']}", "w").write("\n".join(lines))
        r = subprocess.run(["bash", os.path.join(HERE, "run_wp.sh"), d, t, m["function"]],
                           env=dict(os.environ, VP_MUTANT="1"), capture_output=True, text=True)
        caught = r.returncode != 0
        print(f"{m['id']}: {'caught' if caught else 'MISSED'}  ({m['function']})", flush=True)
        if not caught:
            bad.append(m["id"])
        shutil.rmtree(d, ignore_errors=True)
    print("all caught" if not bad else f"missed: {bad}")
    sys.exit(1 if bad else 0)


main()
