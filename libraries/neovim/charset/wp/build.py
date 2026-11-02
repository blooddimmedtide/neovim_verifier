"""Annotated standalone copy of charset.c's string helpers for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c> [--fixed]
--fixed: the checkout is the fixed fork; functions in FIXED_SHA use the fork's pinned
text and drop their "// upstream only" preconditions.
Exact upstream text of each function (sha256 pinned), from charset.c and the
ascii_defs.h inline helpers it calls, with an ACSL contract placed before each
function and annotations inserted as comments. The C code is not changed:
removing the /*@ ... */ comments (and ghost parameters / arguments) gives back
the upstream text, which is checked below.
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import CONTRACTS, LOOPS, LOGIC, GHOST_PARAMS, GHOST_ARGS, PIECES, FIXED_SHA, PRELUDE_EXTRA, PRELUDE_CHECKS
import lemmas, tool_patches

PRELUDE = """\
// Prelude: the system headers charset.c uses (<string.h> replaced by stubs/vp_string.h,
// Neovim's xmalloc by stubs/nvim/memory.h), the constants and macros as Neovim
// defines them (checked against upstream below), FUNC_ATTR_* as nothing.
// Platform: Linux/x86_64, so BACKSLASH_IN_FILENAME is not defined.
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include "vp_string.h"
#include "nvim/memory.h"
#define NUL '\\000'
#define NL '\\012'
#define Ctrl_V 22
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_NONNULL_RET
#define FUNC_ATTR_PURE
#define FUNC_ATTR_CONST
#define FUNC_ATTR_ALWAYS_INLINE
#define FUNC_ATTR_WARN_UNUSED_RESULT
"""
CHECKS = [("src/nvim/ascii_defs.h", "#define NUL             '\\000'"),
          ("src/nvim/ascii_defs.h", "#define NL              '\\012'"),
          ("src/nvim/ascii_defs.h", "#define Ctrl_V          22"),
          ("src/nvim/charset.c", "#include <string.h>")]
GHOST_RE = r" /\*@ ghost \(.*?\) \*/"


def main(tree, out, fixed=False):
    for path, text in CHECKS + PRELUDE_CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    for d in ("BACKSLASH_IN_FILENAME",):
        if re.search(r"#\s*define\s+" + d + r"\b", open(f"{tree}/src/nvim/os/os_defs.h").read()
                     + open(f"{tree}/src/nvim/os/unix_defs.h").read()):
            sys.exit(f"build: {d} is defined on Unix now")
    parts, cache = [PRELUDE, PRELUDE_EXTRA, lemmas.acsl(), LOGIC], {}
    for path, name, want in PIECES:
        lines = cache.setdefault(path, open(f"{tree}/{path}").read().split("\n"))
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if fixed and name in FIXED_SHA:
            want = FIXED_SHA[name]
        if h != want:
            sys.exit(f"build: {name} ({path}:{s + 1}) changed upstream: sha256 {h}")
        patched = tool_patches.apply(name, piece)   # declared rewrites (equiv/ proves them)
        a = patched
        if name in GHOST_PARAMS:
            sig, param = GHOST_PARAMS[name]
            if a.count(sig + "\n") != 1:
                sys.exit(f"build: {name}: signature not found once: {sig!r}")
            a = a.replace(sig + "\n", f"{sig} /*@ ghost ({param}) */\n")
        for call, arg in GHOST_ARGS.get(name, []):
            if a.count(call) != 1:
                sys.exit(f"build: {name}: call not found once: {call!r}")
            a = a.replace(call, f"{call} /*@ ghost ({arg}) */")
        for entry in LOOPS.get(name, []):
            # (anchor, annotation[, nth occurrence (None: must be unique)[, "after"]])
            anchor, annot = entry[0], entry[1]
            nth = entry[2] if len(entry) > 2 else None
            after = len(entry) > 3 and entry[3] == "after"   # insert after the anchor text
            k = a.count(anchor)
            if (nth is None and k != 1) or (nth is not None and k <= nth):
                sys.exit(f"build: {name}: anchor not found {'once' if nth is None else nth + 1}: {anchor!r}")
            pos = -1
            for _ in range((nth or 0) + 1):
                pos = a.index(anchor, pos + 1)
            indent = re.match(r"\s*", anchor).group(0)
            if after:
                end = pos + len(anchor)
                a = a[:end] + f"{indent}/*@ {annot} */\n" + a[end:]
            else:
                a = a[:pos] + f"{indent}/*@ {annot} */\n" + a[pos:]
        stripped = re.sub(GHOST_RE, "", a)
        assert re.sub(r"[ \t]*/\*@.*?\*/\n", "", stripped, flags=re.S) == patched, name
        contract = CONTRACTS[name]
        if fixed:   # upstream-only preconditions (the bug's input range) are dropped
            contract = "\n".join(l for l in contract.split("\n") if "// upstream only" not in l)
        parts.append(f"// {path}:{s + 1} ({'fixed fork' if fixed and name in FIXED_SHA else 'verbatim'}, plus ACSL comments)\n/*@ {contract} */\n{a}\n")
    open(out, "w").write("\n".join(parts))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--fixed" in sys.argv[3:])
