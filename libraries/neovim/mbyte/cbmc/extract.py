"""Pull exact upstream text out of Neovim sources for a standalone proof file.

mbyte.c includes 47 headers, most of them generated during a Neovim build, so
the proof tools cannot read the whole file without a build. The functions proved
here use only a few macros and types from those headers, so this script copies
each function (signature to closing brace), table or type verbatim and puts the
pieces after a short prelude that defines the macros. build.py refuses any piece
whose sha256 differs from the reviewed one, so a changed upstream file cannot be
proved by accident.
"""
import hashlib, re, sys

PRELUDE_CHECKS = [  # upstream definitions the prelude copies
    ("src/nvim/ascii_defs.h", "#define NUL             '\\000'"),
    ("src/nvim/macros_defs.h", "# define EXPECT(cond, value) __builtin_expect((cond), (value))"),
    ("src/nvim/macros_defs.h", "# define MIN(X, Y) ((X) < (Y) ? (X) : (Y))"),
    ("src/nvim/mbyte_defs.h", "  MB_MAXCHAR = 6,"),
    ("src/nvim/mbyte.h", "extern const uint8_t utf8len_tab[256];"),
]
PRELUDE = """\
// Prelude: the macros the copied code uses, as Neovim defines them. EXPECT is
// __builtin_expect in Neovim, which returns its first argument; FUNC_ATTR_* are
// attributes only. MB_MAXCHAR is an enum constant in mbyte_defs.h.
#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#define NUL '\\000'
#define EXPECT(cond, value) (cond)
#define MIN(X, Y) ((X) < (Y) ? (X) : (Y))
enum { MB_MAXCHAR = 6, };
#define FUNC_ATTR_PURE
#define FUNC_ATTR_CONST
#define FUNC_ATTR_ALWAYS_INLINE
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_NONNULL_ARG(...)
#define FUNC_ATTR_NONNULL_RET
"""

# name -> (file, start regex, end regex). Default: a function in mbyte.c ending at "}" in column 0.
SPECIAL = {
    "utf8len_tab": ("src/nvim/mbyte.c", r"^const uint8_t utf8len_tab\[\] = \{$", r"^\};$"),
    "CharBoundsOff": ("src/nvim/mbyte_defs.h", r"^typedef struct \{$", r"^\} CharBoundsOff;$"),
    "utf_is_trail_byte": ("src/nvim/mbyte.h", r"^static inline bool utf_is_trail_byte\(", r"^\}$"),
}


def find_piece(lines, name):
    """Return (start, end), 0-based inclusive."""
    if name in SPECIAL:
        _, sp, ep = SPECIAL[name]
        start_pat, end_pat = re.compile(sp), re.compile(ep)
    else:
        start_pat = re.compile(r"^[A-Za-z_][\w \*]*\b" + re.escape(name) + r"\(")
        end_pat = re.compile(r"^\}")
    starts = [i for i, l in enumerate(lines) if start_pat.match(l)]
    if name == "CharBoundsOff":   # several anonymous structs: take the one ending in the name
        starts = [s for s in starts if any(end_pat.match(l) for l in lines[s:s + 12])
                  and next(i for i in range(s, len(lines)) if lines[i].startswith("}")) ==
                  next(i for i in range(s, len(lines)) if end_pat.match(lines[i]))]
    if len(starts) != 1:
        sys.exit(f"extract: {name}: expected one definition, found {len(starts)}")
    s = starts[0]
    e = s
    while not end_pat.match(lines[e]):
        e += 1
    return s, e


def extract(tree, names):
    for path, text in PRELUDE_CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"extract: {path} no longer contains: {text}")
    cache, out = {}, {}
    for n in names:
        path = SPECIAL.get(n, ("src/nvim/mbyte.c",))[0]
        if path not in cache:
            cache[path] = open(f"{tree}/{path}").read().split("\n")
        s, e = find_piece(cache[path], n)
        piece = "\n".join(cache[path][s:e + 1])
        out[n] = (f"{path}:{s + 1}", piece, hashlib.sha256(piece.encode()).hexdigest())
    return out


if __name__ == "__main__":
    for n, (where, piece, h) in extract(sys.argv[1], sys.argv[2:]).items():
        print(n, where, h)
