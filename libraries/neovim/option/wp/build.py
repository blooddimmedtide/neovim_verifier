"""Annotated standalone copy of option.c's comma-list helpers for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c>
Each function is the exact upstream text, sha256 pinned (upstream 7b87ce8). ACSL is
inserted as comments only, at exact anchor lines; the build checks that removing every
/*@ ... */ comment gives back the upstream text unchanged.
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import LOGIC, CONTRACTS

F = "src/nvim/option.c"
SHA = {  # upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
    "find_key_item": "3b4c9799c3494a13b1b08f10ea3e6933b577b3a678270ae78f5f4a58c26a74b7",
    "remove_comma_item": "bea662804d8907c33b987c125f379acbf7680e79cb47704084bb08aa58294944",
    "append_item": "7ae3f2836992e83927a7a19eaee25bf80ad080e0ea9caacea18a9e22b881260c",
    "prepend_item": "834cbedbdb140eafa9a81c255ffa41caf57ff6c30c08e56777ee9e3821399b17",
}
PRELUDE = """\
// Prelude: types and macros option.c uses here, as Neovim defines them (each line
// checked against the upstream headers by build.py), and contracts for callees.
#include <stddef.h>
#include <stdint.h>
#include "vp_option.h"
#define NUL '\\000'
#define STRMOVE(d, s)       memmove((d), (s), strlen(s) + 1)
"""
CHECKS = [("src/nvim/ascii_defs.h", "#define NUL             '\\000'"),
          ("src/nvim/memory.h", "#define STRMOVE(d, s)       memmove((d), (s), strlen(s) + 1)")]
COMMENT = re.compile(r"\s*/\*@(?:(?!\*/).)*\*/\s*", re.S)  # one ACSL comment, nothing else


def main(tree, out):
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    lines = open(f"{tree}/{F}").read().split("\n")
    parts = [PRELUDE, LOGIC]
    for name, want in SHA.items():
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if h != want:
            sys.exit(f"build: {name} changed upstream: {h}")
        contract, anchors = CONTRACTS[name]
        ann = piece
        for anchor, text, where in anchors:
            if not COMMENT.fullmatch(text):
                sys.exit(f"build: {name}: annotation is not a single ACSL comment: {text!r}")
            if ann.count(anchor) != 1:
                sys.exit(f"build: {name}: anchor not unique: {anchor!r}")
            ann = ann.replace(anchor, text + anchor if where == "before" else anchor + text)
        stripped = ann
        for _, text, _ in anchors:
            stripped = stripped.replace(text, "", 1)
        if stripped != piece:
            sys.exit(f"build: {name}: annotations change the code")
        parts.append(contract + ann)
    open(out, "w").write("\n".join(parts) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
