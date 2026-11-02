"""Annotated standalone copy of hashtab.c for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c> [upstream|fixed] [function]
Each function is the exact upstream (or fixed-fork) text, sha256 pinned. The build
  1. applies the declared tool patches (tool_patches.py; each proved equal to the
     original in ../equiv/);
  2. inserts ACSL as comments only, and checks that removing every /*@ ... */ gives back
     the text of step 1 exactly.
The prelude copies the types and macros hashtab.c uses; each copied line is checked
against the upstream headers.
"""
import hashlib, os, re, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import LOGIC, contracts, annotations, GHOST, HELPERS
from tool_patches import PATCHES
import bvlemmas

F = "src/nvim/hashtab.c"
SHA = {  # upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd, in file order
    "hash_init": "ae22920287819f7c715f39be623dd3efb5441ba004dc3bc3623a99352555c062",
    "hash_clear": "73b5c3e17352fe1a2511c4bfa1ef7ff51b6df6467deb7e8cacf961a175a0af8a",
    "hash_clear_all": "67d62859b73db7fb75232026132ad8988356bfdd0ca15df9c080e00e894ef8d1",
    "hash_find": "3f3d6572d331852ae4ecfbf602aa305d807aea783e262ff5abde77f6b6a2d352",
    "hash_find_len": "3a1da29c742c8c6c10264c5b3326f62b15add9f36aa96776a884fa1f48c14fc6",
    "hash_lookup": "cb261804333c54ee33be76d9e7395556e9837217df89e2cf6834fa69164bbb1e",
    "hash_debug_results": "40371518b05f3204709080532d2ea02bc741919ba7c344b301537870a5eeecaf",
    "hash_add": "6330bc73a3b6d403cb7ccf9143a257ed59e76e9a0830704703ff8e0c357e33b9",
    "hash_add_item": "a6fe20ad7f68a25c9da73d8aaa3720e943263763f5b41ee31da45e2473e2d74e",
    "hash_remove": "da05e277becd047f68f536a73783449d5095e7427498b492e961cf4718a7b381",
    "hash_lock": "552e9056c07cf9b8d5d9076a99d3107b9f9357b41be663051030a3de86304519",
    "hash_unlock": "9f8bed7a8da3ac68a23b6601933b451b1dc0f23b4b2808215b4f702a6f062528",
    "hash_may_resize": "a6453045c80fbfa1f288bb42019702dbcc061980daa0ab436e31aa0b6b5983c5",
    "hash_hash": "7dceaf49658740c11f9d82ecc40e50dd14a2dd3109845612be7e722fc064b27a",
    "hash_hash_len": "ec0c4f67f11353cf935ac11db5b330744ac86c23c1bea25923df300071e0639c",
    "_hash_key_removed": "f2b247d7fef6e0c0c9fcec3824b0c8723abdd8c7e1d8aa63da96cb4f3d29dd58",
}
FIXED_SHA = {}
PRELUDE = """\
// Prelude: hashtab.c's system headers (<string.h> replaced by vp_string.h), the types
// of hashtab_defs.h and the macros hashtab.c uses, as Neovim defines them (each line
// checked against the upstream text by build.py), and stubs for what it calls.
#include <assert.h>
#include <inttypes.h>
#include <stdbool.h>
#include "vp_hashtab.h"
#define NUL '\\000'
#define MAX(X, Y) ((X) > (Y) ? (X) : (Y))
#define OK                     1
#define FAIL                    0
#define _(x) ((char *)(x))
#define FUNC_ATTR_PURE
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define CLEAR_FIELD(field)  memset(&(field), 0, sizeof(field))
#define CLEAR_POINTER(ptr)  memset((ptr), 0, sizeof(*(ptr)))
"""
TYPES_FROM = "src/nvim/hashtab_defs.h"
HEADER_FROM = "src/nvim/hashtab.h"
CHECKS = [("src/nvim/macros_defs.h", "# define MAX(X, Y) ((X) > (Y) ? (X) : (Y))"),
          ("src/nvim/ascii_defs.h", "#define NUL             '\\000'"),
          ("src/nvim/vim_defs.h", "# define OK                     1"),
          ("src/nvim/vim_defs.h", "#define FAIL                    0"),
          ("src/nvim/gettext_defs.h", "# define _(x) ((char *)(x))  // NOLINT(bugprone-reserved-identifier)"),
          ("src/nvim/memory.h", "#define CLEAR_FIELD(field)  memset(&(field), 0, sizeof(field))"),
          ("src/nvim/memory.h", "#define CLEAR_POINTER(ptr)  memset((ptr), 0, sizeof(*(ptr)))"),
          ("src/nvim/hashtab.h", "extern char hash_removed;"),
          ("src/nvim/hashtab.h", "#define HI_KEY_REMOVED (&hash_removed)"),
          ("src/nvim/hashtab.h", "#define HASHITEM_EMPTY(hi) ((hi)->hi_key == NULL || (hi)->hi_key == &hash_removed)"),
          (F, "#define PERTURB_SHIFT 5"),
          (F, "#define HASH_CYCLE_BODY(hash, p) \\"),
          (F, "  hash = hash * 101 + *p++"),
          (F, "char hash_removed;")]
# hashtab_defs.h minus its #pragma/#include lines, verbatim
HEADER_LINES = ["extern char hash_removed;", "#define HI_KEY_REMOVED (&hash_removed)",
                "#define HASHITEM_EMPTY(hi) ((hi)->hi_key == NULL || (hi)->hi_key == &hash_removed)",
                "#define PERTURB_SHIFT 5", "#define HASH_CYCLE_BODY(hash, p) \\", "  hash = hash * 101 + *p++",
                "char hash_removed;", '#include "vp_hashtab_calloc.h"']


def strip(s):
    c = r"/\*@(?:(?!\*/).)*\*/"   # one annotation comment (no */ inside)
    s = re.sub(r"^[ \t]*" + c + r"\n", "", s, flags=re.S | re.M)
    s = re.sub(r" " + c, "", s, flags=re.S)
    return re.sub(c + r" ", "", s, flags=re.S)


def main(tree, out, mode="upstream", only=None):
    fixed = mode == "fixed"
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    types = [l for l in open(f"{tree}/{TYPES_FROM}").read().split("\n")
             if not l.startswith(("#pragma", "#include"))]
    lines = open(f"{tree}/{F}").read().split("\n")
    C, A = contracts(fixed), annotations(fixed)
    prelude = PRELUDE + "\n".join(types) + "\n" + "\n".join(HEADER_LINES) + "\n"
    parts, missing = [prelude, bvlemmas.ghost(), LOGIC, GHOST, HELPERS], False
    protos = []
    for name, want in SHA.items():
        if only and name != only:
            continue
        if name not in C:
            print(f"build: {name}: no contract yet, left out (the run fails)", file=sys.stderr)
            missing = True
            continue
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if fixed and name in FIXED_SHA:
            want = FIXED_SHA[name]
        if h != want:
            sys.exit(f"build: {name} ({F}:{s + 1}) differs from the pinned {mode} text: sha256 {h}")
        code = piece
        for old, new in PATCHES.get(name, []):
            if code.count(old) != 1:
                sys.exit(f"build: {name}: tool patch anchor not found once: {old!r}")
            code = code.replace(old, new)
        annotated = code
        for kind, anchor, annot in A.get(name, []):
            if annotated.count(anchor) != 1:
                sys.exit(f"build: {name}: anchor not found once: {anchor!r}")
            if kind == "before":    # a whole line before the anchor line
                indent = re.match(r"\s*", anchor).group(0)
                annotated = annotated.replace(anchor, f"{indent}/*@ {annot} */\n{anchor}")
            elif kind == "after":   # inline, right after the anchor text
                annotated = annotated.replace(anchor, f"{anchor} /*@ {annot} */")
            elif kind == "inline":  # inline, right before the anchor text
                annotated = annotated.replace(anchor, f"/*@ {annot} */ {anchor}")
            else:
                sys.exit(f"build: bad annotation kind {kind}")
        if strip(annotated) != code:
            sys.exit(f"build: {name}: stripping the annotations does not give the source back")
        # prototype with the same contract, so callers defined earlier see it
        sig = annotated.split("\n{", 1)[0]
        protos.append(f"/*@ {C[name]} */\n{sig};\n")
        parts.append(f"// {F}:{s + 1} ({mode}, verbatim plus ACSL comments"
                     f"{', tool patches applied' if code != piece else ''})\n{annotated}\n")
    open(out, "w").write("\n".join(parts[:5] + protos + parts[5:]))
    if missing:
        sys.exit(2)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], a[2] if len(a) > 2 else "upstream", a[3] if len(a) > 3 else None)
