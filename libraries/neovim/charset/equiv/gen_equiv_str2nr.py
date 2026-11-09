"""Generate the CBMC equivalence harness for vim_str2nr's tool patches.

Usage: python3 -I gen_equiv_str2nr.py <neovim checkout> <out.c> [--fixed]
Compares the exact function text (sha256 pinned in ../wp/contracts.py), compiled by the
real C preprocessor, with the text WP reads (../wp/tool_patches.py: PARSE_NUMBER expanded,
the flattened conditions and the outlined helpers). For every string of L bytes plus NUL (interior NULs allowed,
so every string of length <= L), every maxlen 0..L, every flag value the contract allows, both
values of strict and every choice of NULL / non-NULL outputs with any initial contents, both
versions must store the same values. No __CPROVER_assume.
"""
import hashlib, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "wp"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
import contracts, tool_patches

tree, out = sys.argv[1], sys.argv[2]
fixed = "--fixed" in sys.argv[3:]
want = {n: h for _, n, h in contracts.PIECES}
if fixed:
    want.update(contracts.FIXED_SHA)
src = {}
for f, name, _ in contracts.PIECES:
    if name.startswith("ascii_is") or name in ("hex2nr", "vim_str2nr"):
        lines = open(f"{tree}/{f}").read().split("\n")
        s, e = find(lines, name)
        src[name] = "\n".join(lines[s:e + 1])
        if hashlib.sha256(src[name].encode()).hexdigest() != want[name]:
            sys.exit(f"gen_equiv_str2nr: {name} changed")
orig = src["vim_str2nr"].replace("void vim_str2nr(", "void s_original(", 1)
new = tool_patches.apply("vim_str2nr", src["vim_str2nr"]).replace("void vim_str2nr(", "void s_patched(", 1)
helpers = "\n\n".join(src[n] for n in src if n != "vim_str2nr")
prelude = contracts.PRELUDE_EXTRA.split("// abort()")[0]
open(out, "w").write(f"""#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#define NUL '\\000'
#define FUNC_ATTR_PURE
#define FUNC_ATTR_CONST
#define FUNC_ATTR_ALWAYS_INLINE
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_NONNULL_ALL
{prelude}
{helpers}

{orig}

{new}

#ifndef L
#define L 6
#endif
// every value of what that the precondition allows (tool_patches.STR2NR_WHAT, 44 values)
static const int WHATS[] = {{{", ".join(str(w) for w in tool_patches.STR2NR_WHAT)}}};
int nondet_int(void); unsigned nondet_unsigned(void); bool nondet_bool(void);
int64_t nondet_i64(void); uint64_t nondet_u64(void);
void harness(void) {{
  char s[L + 1];
  for (int i = 0; i < L; i++) s[i] = (char)nondet_int();
  s[L] = NUL;
  int what = WHATS[nondet_unsigned() % (sizeof WHATS / sizeof WHATS[0])];
  int maxlen = (int)(nondet_unsigned() % (L + 1));
  bool strict = nondet_bool();
  int pre0 = nondet_int(), len0 = nondet_int(); int64_t n0 = nondet_i64(); uint64_t u0 = nondet_u64();
  bool o0 = nondet_bool();
  bool hp = nondet_bool(), hl = nondet_bool(), hn = nondet_bool(), hu = nondet_bool(), ho = nondet_bool();
  int pa = pre0, pb = pre0, la = len0, lb = len0; int64_t na = n0, nb = n0; uint64_t ua = u0, ub = u0;
  bool oa = o0, ob = o0;
  s_original(s, hp ? &pa : NULL, hl ? &la : NULL, what, hn ? &na : NULL, hu ? &ua : NULL, maxlen, strict, ho ? &oa : NULL);
  s_patched(s, hp ? &pb : NULL, hl ? &lb : NULL, what, hn ? &nb : NULL, hu ? &ub : NULL, maxlen, strict, ho ? &ob : NULL);
  __CPROVER_assert(pa == pb && la == lb && na == nb && ua == ub && oa == ob, "patched vim_str2nr stores the same values");
}}
""")
