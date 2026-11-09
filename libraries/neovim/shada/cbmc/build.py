"""Write a standalone C file holding exact upstream text from src/nvim/shada.c.

Usage: python3 -I build.py <neovim checkout> <out.c>
Each function is copied verbatim (signature line to the closing brace in column 0)
and checked against the sha256 below; an upstream change stops the build.
"""
import hashlib, re, sys

REVIEWED = {
    "vim_be64toh": "aef2e0471516cfee8af9a0551146865afa13bb28bc0fcc0a1ca425aa60c560df",
    "fread_len": "fad233abb28876f2eee36f9899bc3e2f6406801af4a999b2abbfc9de5ece6cdd",
    "msgpack_read_uint64": "bff38afa16c9150b968f24cc929005cd38e09c8d30fd13ebff80a96e414e2626",
    "sd_reader_skip": "e4bcdfbed398b43e72c84814e6b9ba372ad7fa17d9b58108fd2b8096abdcdc6f",
    "shada_check_status": "c6f61a236da2ac39792aa359cc738f434223649453c41f4ecc9a815178814667",
}
FIXED = {}

PRELUDE = r"""
// Prelude: types and macros the copied code uses. ShaDaReadResult is copied from
// shada.c. FileDescriptor is the abstract model in model.h. _() is gettext,
// semsg only prints. HAVE_BE64TOH is undefined and ORDER_BIG_ENDIAN too
// (x86_64), so the portable vim_be64toh loop is the one Neovim uses there.
#include <assert.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "model.h"
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_NONNULL_ALL
#define _(x) (x)
#define RERR "E575: "
#define RCERR "E576: "
#define SERR "E886: "
enum { MPACK_OK = 0, MPACK_EOF = 1, MPACK_ERROR = 2 };
"""

def piece(lines, name):
    if name == "ShaDaReadResult":
        e = next(i for i, l in enumerate(lines) if l.startswith("} ShaDaReadResult;"))
        s = max(i for i in range(e) if lines[i].startswith("typedef enum {"))
        return s, e
    pat = re.compile(r"^(static )?(inline )?[A-Za-z_][\w \*]*\b" + re.escape(name) + r"\(")
    s = [i for i, l in enumerate(lines) if pat.match(l)]
    if len(s) != 1:
        sys.exit(f"build: {name}: {len(s)} definitions")
    e = next(i for i in range(s[0], len(lines)) if lines[i].startswith("}"))
    return s[0], e

def main(tree, out, show=False):
    lines = open(f"{tree}/src/nvim/shada.c").read().split("\n")
    parts = [PRELUDE]
    for name in ["ShaDaReadResult"] + list(REVIEWED):
        s, e = piece(lines, name)
        text = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(text.encode()).hexdigest()
        if show:
            print(name, h)
        elif name in FIXED and h == FIXED[name][0]:
            parts.append(f"#define {FIXED[name][1]} 1  // fixed fork version")
        elif name != "ShaDaReadResult" and h != REVIEWED[name]:
            sys.exit(f"build: {name} (shada.c:{s+1}) changed upstream: sha256 {h}")
        parts.append(f"// src/nvim/shada.c:{s+1} (verbatim)\n{text}\n")
        if name == "vim_be64toh":
            parts.append("#undef be64toh\n#define be64toh vim_be64toh  // as shada.c does after the definition\n")
    open(out, "w").write("\n".join(parts))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], len(sys.argv) > 3)
