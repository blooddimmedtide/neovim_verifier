"""Copy the tabstop helpers of src/nvim/indent.c verbatim into one standalone file.
Usage: python3 -I extract.py <neovim checkout> <out.c>
Each function (signature line to the first "}" in column 0) is checked against its
reviewed sha256, so a changed upstream file cannot be proved by accident."""
import hashlib, re, sys
NAMES = ["tabstop_padding", "tabstop_at", "tabstop_start", "tabstop_fromto",
         "tabstop_copy", "tabstop_count", "tabstop_first"]
PINS = {}  # filled from pins.txt
PRELUDE = """\
// Prelude: types and macros the copied code uses, as Neovim defines them
// (pos_defs.h: colnr_T is int; types_defs.h: OptInt is int64_t). FUNC_ATTR_* are attributes only.
// curbuf: tabstop_fromto reads only curbuf->b_p_ts, so the harness provides that one field.
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
typedef int colnr_T;
typedef int64_t OptInt;
#define FUNC_ATTR_PURE
typedef struct { OptInt b_p_ts; } buf_T;
extern buf_T *curbuf;
void *xmalloc(size_t size);
"""
def main():
    nv, out = sys.argv[1], sys.argv[2]
    lines = open(nv + "/src/nvim/indent.c").read().split("\n")
    pins = dict(l.split() for l in open(__file__.rsplit("/", 1)[0] + "/pins.txt") if l.strip()) if len(sys.argv) < 4 else {}
    parts, newpins = [PRELUDE], []
    for n in NAMES:
        s = [i for i, l in enumerate(lines) if re.match(r"^[A-Za-z_][\w \*]*\b" + n + r"\(", l)]
        assert len(s) == 1, n
        e = next(i for i in range(s[0], len(lines)) if lines[i].startswith("}"))
        txt = "\n".join(lines[s[0]:e + 1]) + "\n"
        h = hashlib.sha256(txt.encode()).hexdigest()
        newpins.append(f"{n} {h}")
        if pins and pins.get(n) != h:
            sys.exit(f"{n}: sha256 {h} differs from pinned {pins.get(n)}")
        parts.append(txt)
    open(out, "w").write("\n".join(parts))
    if not pins:
        print("\n".join(newpins))
main()
