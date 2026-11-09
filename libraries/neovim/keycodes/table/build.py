"""Standalone copy for CBMC of the key-name lookups in keycodes.c.

Usage: python3 -I build.py <neovim checkout> <out dir>
Writes out/kt.c: keycodes.h and ascii_defs.h (verbatim, #include lines dropped), the
macros they need from macros_defs.h (checked verbatim), the generated key_names_table
(gen_keycodes.lua run by gen.sh), vim_strnicmp_asc (strings.c), and
find_special_key_in_table / get_special_key_code (keycodes.c), each sha256 pinned.
"""
import hashlib, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools"))
from extract_c import find

PIECES = [("src/nvim/strings.c", "vim_strnicmp_asc", "2eea2aad5190c0448d77fbec55c0521a541ddd083186d13de8af54f465c5f87a"),
          ("src/nvim/keycodes.c", "find_special_key_in_table", "298bf785ba989f4886f04c249f5a0a8b244d45a3d3d88d45d0244412b3a3bf5c"),
          ("src/nvim/keycodes.c", "get_special_key_code", "278b910b659b56122ee25c3ed9a0bbf7474b92a3662fd19bb87b9919728c9137")]
MACROS = ["#define TOLOWER_ASC(c) (((c) < 'A' || (c) > 'Z') ? (c) : (c) + ('a' - 'A'))",
          "#define ASCII_ISLOWER(c) ((unsigned)(c) >= 'a' && (unsigned)(c) <= 'z')",
          "#define ASCII_ISUPPER(c) ((unsigned)(c) >= 'A' && (unsigned)(c) <= 'Z')",
          "#define ASCII_ISALPHA(c) (ASCII_ISUPPER(c) || ASCII_ISLOWER(c))",
          "#define ASCII_ISALNUM(c) (ASCII_ISALPHA(c) || ascii_isdigit(c))",
          "#define ARRAY_SIZE(arr) \\\n  ((sizeof(arr)/sizeof((arr)[0])) \\\n   / ((size_t)(!(sizeof(arr) % sizeof((arr)[0])))))"]


def strip(path):
    return "\n".join(l for l in open(path).read().split("\n")
                     if not l.startswith("#include") and not l.startswith("#pragma"))


def main():
    tree, out, pin = sys.argv[1], sys.argv[2], "--pin" in sys.argv
    md = open(f"{tree}/src/nvim/macros_defs.h").read()
    for m in MACROS:
        if m.replace("#define ", "# define ", 0) not in md and m not in md:
            # macros_defs.h indents some defines as "# define"
            if m.replace("#define", "# define") not in md:
                sys.exit(f"build: macros_defs.h no longer has {m}")
    parts = ["#include <stdint.h>\n#include <stdbool.h>\n#include <stddef.h>\n#include <limits.h>",
             "typedef struct { char *data; size_t size; } String;  // api/private/defs.h",
             "#define FUNC_ATTR_CONST\n#define FUNC_ATTR_ALWAYS_INLINE\n#define FUNC_ATTR_PURE\n"
             "#define FUNC_ATTR_WARN_UNUSED_RESULT\n#define FUNC_ATTR_NONNULL_ALL",
             "\n".join(MACROS),
             strip(f"{tree}/src/nvim/ascii_defs.h"), strip(f"{tree}/src/nvim/keycodes.h"),
             "int vim_strnicmp_asc(const char *s1, const char *s2, size_t len);",
             open(f"{out}/keycode_names.generated.h").read()]
    for path, name, want in PIECES:
        lines = open(f"{tree}/{path}").read().split("\n")
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if pin:
            print(name, h)
        elif h != want:
            sys.exit(f"build: {name} changed upstream: {h}")
        parts.append(piece)
    open(f"{out}/kt.c", "w").write("\n\n".join(parts) + "\n")


main()
