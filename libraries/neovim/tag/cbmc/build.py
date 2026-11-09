"""Write a standalone C file holding exact upstream text from src/nvim/tag.c and
src/nvim/strings.c (vim_strchr). Usage: python3 -I build.py <neovim checkout> <out.c>
Each piece is pinned by sha256; an upstream change stops the build until reviewed."""
import hashlib, re, sys

PIECES = {  # name -> (file, sha256 of the verbatim text)
    "vim_strchr": ("src/nvim/strings.c", None),
    "tag_strnicmp": ("src/nvim/tag.c", None),
    "parse_tag_line": ("src/nvim/tag.c", None),
    "test_for_static": ("src/nvim/tag.c", None),
    "matching_line_len": ("src/nvim/tag.c", None),
}
PINS = {  # reviewed on neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
    "vim_strchr": "137e45091b810de2f53d06eda77e84c0b33d6b87084af8460126549013c5c946",
    "tag_strnicmp": "3811ffe5b0fc2c01ecd4e4774754d09e118ef02ee5a1b35e9f9c525ef7aa4c0d",
    "parse_tag_line": "625bd0692550314c9f9f83bf7ea4c8b1978bd251f4e7b788f118633ac0212c22",
    "test_for_static": "bd0408131e1208c3887c504404c065b4279054eb4a92eb0624f0493c83cffb42",
    "matching_line_len": "ab0b99ba4b2a975bb4ba2967d459c7224bedf6b73c87e293929e7a17f8d847c1",
}
PRELUDE = """\
// Prelude: macros and types the copied code uses, as Neovim defines them
// (ascii_defs.h TAB/NUL, vim_defs.h OK/FAIL, macros_defs.h TOUPPER_ASC,
// mbyte_defs.h MB_MAXBYTES, pos_defs.h linenr_T). FUNC_ATTR_* are attributes only.
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#ifndef NV_REAL_LIBC
#include "libc.h"
#endif
#define NUL '\\000'
#define TAB '\\011'
#define OK 1
#define FAIL 0
#define TOUPPER_ASC(c) (((c) < 'a' || (c) > 'z') ? (c) : (c) - ('a' - 'A'))
enum { MB_MAXBYTES = 21, };
typedef int32_t linenr_T;
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_PURE
#define FUNC_ATTR_WARN_UNUSED_RESULT
// Only reached for c >= 0x80; the tag helpers pass TAB, '\\t' and ':'.
static int utf_char2bytes(const int c, char *const buf) { assert(0 && "unreachable"); return 0; }
"""

def piece(tree, f, name):
    lines = open(f"{tree}/{f}").read().split("\n")
    pat = re.compile(r"^(static )?[A-Za-z_][\w \*]*\b" + re.escape(name) + r"\(")
    s = [i for i, l in enumerate(lines) if pat.match(l)]
    assert len(s) == 1, (name, s)
    e = next(i for i in range(s[0], len(lines)) if lines[i] == "}")
    txt = "\n".join(lines[s[0]:e + 1])
    return f"{f}:{s[0]+1}", txt, hashlib.sha256(txt.encode()).hexdigest()

def main(tree, out, pins_only=False):
    parts = [PRELUDE, open(__file__.replace("build.py", "types.h")).read()]
    for name, (f, _) in PIECES.items():
        where, txt, h = piece(tree, f, name)
        if pins_only:
            print(f'    "{name}": "{h}",'); continue
        if PINS.get(name) != h:
            sys.exit(f"build: {name} ({where}) changed: sha256 {h}")
        parts.append(f"// {where} (verbatim)\n{txt}\n")
    if not pins_only:
        open(out, "w").write("\n".join(parts))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, sys.argv[1:2] and len(sys.argv) == 2)
