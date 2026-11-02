"""Annotated standalone copy of regexp.c's getdecchrs for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c>
The checkout is the pinned upstream commit or the fixed fork; the function's sha256
says which, and picks the matching contract. Exact text, with ACSL only in comments:
removing the /*@ ... */ comments gives back the checkout's text (checked below).
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import CONTRACTS, LOOPS, LOGIC, GHOST_PARAMS

F = "src/nvim/regexp.c"
SHA = {  # name -> {sha256: variant}
    "getdecchrs": {
        "33b5ef63b69863fbfbd11310f4747611d4809d230c6b043feca6085d6c4fe2eb": "upstream",
        "b7ac7ec2bdbc39fc91f509b9d2b5d0fbbfd3fd007983408d2bda47bbb4725645": "fixed",
    },
}
# The two globals the function uses, declared as in regexp.c.
PRELUDE = """\
// Prelude: the headers and globals getdecchrs uses, as regexp.c declares them.
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>
#include <inttypes.h>
static char *regparse;          ///< Input-scan pointer.
static int curchr;              // currently parsed character
"""
CHECKS = [(F, "static char *regparse;          ///< Input-scan pointer."),
          (F, "static int curchr;              // currently parsed character"),
          (F, "#include <limits.h>"), (F, "#include <stdbool.h>"), (F, "#include <stddef.h>"), (F, "#include <inttypes.h>")]


def main(tree, out):
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    lines = open(f"{tree}/{F}").read().split("\n")
    parts = [PRELUDE, LOGIC]
    variants = []
    for name, shas in SHA.items():
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if h not in shas:
            sys.exit(f"build: {name} ({F}:{s + 1}) changed: sha256 {h}")
        key = f"{name}/{shas[h]}"
        variants.append(key)
        annotated = piece
        if name in GHOST_PARAMS:
            sig, param = GHOST_PARAMS[name]
            if annotated.count(sig + "\n") != 1:
                sys.exit(f"build: {name}: signature not found once: {sig!r}")
            annotated = annotated.replace(sig + "\n", f"{sig} /*@ ghost ({param}) */\n")
        for anchor, annot in LOOPS.get(key, []):
            if annotated.count(anchor) != 1:
                sys.exit(f"build: {key}: anchor not found once: {anchor!r}")
            indent = re.match(r"\s*", anchor).group(0)
            annotated = annotated.replace(anchor, f"{indent}/*@ {annot} */\n{anchor}")
        stripped = re.sub(r" /\*@ ghost \([^)]*\) \*/\n", "\n", annotated)
        assert re.sub(r"[ \t]*/\*@.*?\*/\n", "", stripped, flags=re.S) == piece, name
        parts.append(f"// {F}:{s + 1} ({shas[h]}, verbatim, plus ACSL comments)\n/*@ {CONTRACTS[key]} */\n{annotated}\n")
    open(out, "w").write("\n".join(parts))
    print("variants:", " ".join(variants))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
