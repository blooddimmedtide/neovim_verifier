"""Generate the CBMC equivalence harness for the backslash_halve tool patch.

Usage: python3 -I gen_equiv.py <neovim checkout> <out.c>
Takes the exact upstream backslash_halve (sha256 pinned in ../wp/contracts.py) and the
patched text (../wp/tool_patches.py), renames them, and checks they leave identical
buffers for every byte content of a buffer of L bytes plus a final NUL. Interior NULs
are allowed, so this covers every string of length <= L. No __CPROVER_assume.
"""
import hashlib, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "wp"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
import contracts, tool_patches

tree, out = sys.argv[1], sys.argv[2]
want = {n: h for _, n, h in contracts.PIECES}
lines = open(f"{tree}/src/nvim/charset.c").read().split("\n")
pieces = {}
for name in ("rem_backslash", "backslash_halve"):
    s, e = find(lines, name)
    pieces[name] = "\n".join(lines[s:e + 1])
    if hashlib.sha256(pieces[name].encode()).hexdigest() != want[name]:
        sys.exit(f"gen_equiv: {name} changed upstream")
orig = pieces["backslash_halve"].replace("void backslash_halve(", "void bh_original(", 1)
new = tool_patches.apply("backslash_halve", pieces["backslash_halve"]).replace(
    "void backslash_halve(", "void bh_patched(", 1)
open(out, "w").write(f"""#include <stdbool.h>
#include <stdint.h>
#define NUL '\\000'
#define FUNC_ATTR_PURE
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_NONNULL_ALL
{pieces["rem_backslash"]}

{orig}

{new}

#ifndef L
#define L 12
#endif
void harness(void) {{
  char a[L + 1], b[L + 1];
  for (int i = 0; i < L; i++) {{ char c; a[i] = c; b[i] = c; }}   // c: any value
  a[L] = NUL; b[L] = NUL;
  bh_original(a);
  bh_patched(b);
  for (int i = 0; i <= L; i++) __CPROVER_assert(a[i] == b[i], "patched backslash_halve leaves the same bytes");
}}
""")
