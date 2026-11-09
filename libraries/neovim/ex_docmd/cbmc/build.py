"""Write a standalone C file holding exact upstream text from src/nvim/ex_docmd.c and charset.c.

Usage: python3 -I build.py <neovim checkout> <out.c>
Each function is cut out by brace matching and checked against the sha256 below;
any upstream change stops the build until the piece is reviewed again.
"""
import hashlib, re, sys

PIECES = [  # (file, function name, sha256 of the verbatim text)
    ("src/nvim/charset.c", "skipwhite", None),
    ("src/nvim/charset.c", "skipdigits", None),
    ("src/nvim/ex_docmd.c", "skip_colon_white", None),
    ("src/nvim/ex_docmd.c", "checkforcmd", None),
    ("src/nvim/ex_docmd.c", "ends_excmd", None),
    ("src/nvim/ex_docmd.c", "find_nextcmd", None),
    ("src/nvim/ex_docmd.c", "check_nextcmd", None),
    ("src/nvim/ex_docmd.c", "cmdmods", None),
    ("src/nvim/ex_docmd.c", "modifier_len", None),
    ("src/nvim/ex_docmd.c", "one_letter_cmd", None),
    ("src/nvim/ex_docmd.c", "parse_bang", None),
]
REVIEWED = {}  # filled from pins.txt

PRELUDE = """\
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
// src/nvim/ascii_defs.h:18 and :84 (copied)
#define NUL '\\000'
static inline bool ascii_iswhite(int c) { return c == ' ' || c == '\\t'; }
// src/nvim/macros_defs.h:48-50 (copied)
#define ASCII_ISLOWER(c) ((unsigned)(c) >= 'a' && (unsigned)(c) <= 'z')
#define ASCII_ISUPPER(c) ((unsigned)(c) >= 'A' && (unsigned)(c) <= 'Z')
#define ASCII_ISALPHA(c) (ASCII_ISUPPER(c) || ASCII_ISLOWER(c))
static inline bool ascii_isdigit(int c) { return c >= '0' && c <= '9'; }  // ascii_defs.h:117
// src/nvim/macros_defs.h:74 (copied)
#define ARRAY_SIZE(arr) \
  ((sizeof(arr)/sizeof((arr)[0])) \
   / ((size_t)(!(sizeof(arr) % sizeof((arr)[0])))))
// Model of the generated command index (ex_cmds_enum.generated.h): only distinct values
// matter to these functions; the harness lets cmdidx be any int.
typedef int cmdidx_T;
enum { CMD_k = 1000, CMD_substitute, CMD_smagic, CMD_snomagic };
// exarg_T (ex_cmds_defs.h) cut down to the one field parse_bang reads.
typedef struct { cmdidx_T cmdidx; } exarg_T;
#define FUNC_ATTR_PURE
#define FUNC_ATTR_CONST
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_NONNULL_RET
"""

def cut(lines, name):
    pat = re.compile(r"^(static )?[A-Za-z_][A-Za-z_ *]*\b" + re.escape(name) + r"\(")
    if name == "cmdmods":  # the modifier table: from "static struct cmdmod {" to "};"
        i = lines.index("static struct cmdmod {")
        j = lines.index("};", i)
        return i + 1, "\n".join(lines[i:j + 1])
    for i, l in enumerate(lines):
        if pat.match(l):
            depth, j, seen = 0, i, False
            while True:
                depth += lines[j].count("{") - lines[j].count("}")
                seen = seen or "{" in lines[j]
                if seen and depth == 0:
                    return i + 1, "\n".join(lines[i:j + 1])
                j += 1
    sys.exit(f"build: {name} not found")

def main(tree, out, pins="pins.txt"):
    want = dict(l.split() for l in open(pins).read().splitlines() if l.strip())
    parts, cache = [PRELUDE], {}
    for path, name, _ in PIECES:
        lines = cache.setdefault(path, open(f"{tree}/{path}").read().split("\n"))
        line, text = cut(lines, name)
        h = hashlib.sha256(text.encode()).hexdigest()
        if want.get(name) != h:
            sys.exit(f"build: {name} ({path}:{line}) sha256 {h} not reviewed")
        parts.append(f"// {path}:{line} (verbatim)\n{text}\n")
    open(out, "w").write("\n".join(parts))

if __name__ == "__main__":
    main(*sys.argv[1:])
