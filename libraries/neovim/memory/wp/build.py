"""Annotated standalone copy of memory.c's string functions for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c>
Exact upstream text (sha256 pinned), with an ACSL contract placed before each
function and loop annotations inserted as comments before exact anchor lines.
The C code itself is not changed: removing the /*@ ... */ comments gives back
the upstream text (checked below).
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
import hashlib

F = "src/nvim/memory.c"
SHA = {
    "xmemcpyz": "0cfa5e88e25bd68bbb8a7784e2df275697d719405f65c2873379d16ce0e23513",
    "xstrnlen": "254115d15d99040b21bd9cd61d823992d6c42f33b5212fd4a0e54b94aaebcbce",
    "xstrchrnul": "3add3192d6f17bdc04315af54c1946b05585a0d73526fc656d213977535e72c7",
    "xmemscan": "96033f1c4de311a53b5ca6c3d990c322272c3c28af522fd97a6ef9d763aad652",
    "strchrsub": "ed937914bc1e8c5fee0ea609222e56ea5a394302e2493c7ccbbb8ffa7292533b",
    "memchrsub": "84726b2b578ed77118af44134608a41b8e0c97b4441823aec3e5b39c3992acf9",
    "strcnt": "5982666748851efc8ced44dc25b0e676d6583b4c3bd1baa776035e8126c2c1af",
    "memcnt": "725abf49ece822db618010dbe630eeae9129e013d0cd47c782fef0f395eb3d6a",
    "xstpcpy": "9f1e7b97575af30539bd95dfcfba0b3899c8a2d185dc4194381c4373e11db1f7",
    "xstpncpy": "5bd5e2b35dd1e232b03fe851879cd091e6c13fce45dc77c2205ff1ab8a670492",
    "xstrlcpy": "6c60c92e9cb1bc77f698fd67c14e661606b6955cf7441eb817f9783bb57f2a95",
    "xstrlcat": "39481ea9e0812d7992d51cdfb93e77a7658ebc81e5b33a23d541605e02a5600c",
    "xmemrchr": "a30beeb9343f8f02bed044487799770847a90e031cbc4d173a20d2b044db7d2f",
    "strequal": "4c1199054d68847fb6080d27af431047f64056617e7c22fa6c31a9e9374ea6b3",
    "strnequal": "8514ed116016b8f39f07647dd3677ee54dc57ca5ca775993c3dd024f77a612fd",
}
PRELUDE = """\
// Prelude: memory.c's system headers (<string.h> replaced by stubs/vp_string.h),
// NUL and MIN as Neovim defines them, FUNC_ATTR_* as nothing.
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include "vp_string.h"   // contracts for <string.h>; no other header here includes it
#define NUL '\\000'
#define MIN(X, Y) ((X) < (Y) ? (X) : (Y))
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_NONNULL_RET
#define FUNC_ATTR_PURE
#define FUNC_ATTR_WARN_UNUSED_RESULT
"""
CHECKS = [("src/nvim/ascii_defs.h", "#define NUL             '\\000'"),
          ("src/nvim/macros_defs.h", "# define MIN(X, Y) ((X) < (Y) ? (X) : (Y))"),
          (F, "#include <string.h>"), (F, "#include <assert.h>")]

from contracts import CONTRACTS, LOOPS, LOGIC, GHOST_PARAMS


def main(tree, out, only=None):
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    lines = open(f"{tree}/{F}").read().split("\n")
    parts = [PRELUDE, LOGIC]
    for name, want in SHA.items():
        if only and name != only:
            continue
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if h != want:
            sys.exit(f"build: {name} ({F}:{s + 1}) changed upstream: sha256 {h}")
        annotated = piece
        if name in GHOST_PARAMS:
            sig, param = GHOST_PARAMS[name]
            if annotated.count(sig + "\n") != 1:
                sys.exit(f"build: {name}: signature not found once: {sig!r}")
            annotated = annotated.replace(sig + "\n", f"{sig} /*@ ghost ({param}) */\n")
        for anchor, annot in LOOPS.get(name, []):
            if anchor == "<END>":   # just before the function's closing brace
                assert annotated.endswith("\n}"), name
                annotated = annotated[:-1] + f"  /*@ {annot} */\n}}"
                continue
            if annotated.count(anchor) != 1:
                sys.exit(f"build: {name}: loop anchor not found once: {anchor!r}")
            indent = re.match(r"\s*", anchor).group(0)
            annotated = annotated.replace(anchor, f"{indent}/*@ {annot} */\n{anchor}")
        stripped = re.sub(r" /\*@ ghost \([^)]*\) \*/\n", "\n", annotated)
        assert re.sub(r"[ \t]*/\*@.*?\*/\n", "", stripped, flags=re.S) == piece, name
        parts.append(f"// {F}:{s + 1} (verbatim, plus ACSL comments)\n/*@ {CONTRACTS[name]} */\n{annotated}\n")
    open(out, "w").write("\n".join(parts))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
