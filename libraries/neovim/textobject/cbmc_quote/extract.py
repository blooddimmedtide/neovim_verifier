"""Copy find_next_quote() and find_prev_quote() verbatim from src/nvim/textobject.c,
check their sha256 pins, and prepend the ASCII fast paths of the two mbyte.c callees
(also copied verbatim and pinned). Any other path of a callee is an assertion
failure, so the proof shows those paths are never reached on ASCII lines."""
import hashlib, re, sys
nv = sys.argv[1]
def grab(path, sig):
    src = open(f"{nv}/{path}").read()
    m = re.search("^" + re.escape(sig) + r"\n.*?^\}\n", src, re.S | re.M)
    if not m: sys.exit(f"{sig} not found")
    return m.group(0)
parts = [grab("src/nvim/textobject.c", "static int find_next_quote(char *line, int col, int quotechar, char *escape)"),
         grab("src/nvim/textobject.c", "static int find_prev_quote(char *line, int col_start, int quotechar, char *escape)")]
uc = grab("src/nvim/mbyte.c", "int utfc_ptr2len(const char *const p)")
uh = grab("src/nvim/mbyte.c", "int utf_head_off(const char *base_in, const char *p_in)")
FAST_UC = "  uint8_t b0 = (uint8_t)(*p);\n\n  if (b0 == NUL) {\n    return 0;\n  }\n  if (b0 < 0x80 && (uint8_t)p[1] < 0x80) {  // be quick for ASCII\n    return 1;\n  }\n"
FAST_UH = "  if ((uint8_t)(*p_in) < 0x80) {              // be quick for ASCII\n    return 0;\n  }\n"
assert FAST_UC in uc and FAST_UH in uh, "callee fast path changed"
PINS = ["4933f3b1dd69f043270278c0046221888f6be8301f437ae227705c9f77fd209e",  # find_next_quote, 7b87ce8
        "7fd64e7af691147d7e69dce975eec15b908bd98bae44d6d3f30b4b1a23c942d5"]  # find_prev_quote, 7b87ce8
for p, want in zip(parts, PINS):
    h = hashlib.sha256(p.encode()).hexdigest()
    if h != want: sys.exit(f"sha256 {h} != pinned {want}")
pre = ("#include <stdbool.h>\n#include <stdint.h>\n#include <string.h>\n#define NUL '\\000'\n"
       "static char *vim_strchr(const char *const string, const int c)\n"
       "{ // strings.c, c < 0x80 branch only (escape and line are ASCII here)\n"
       "  if (c <= 0) {\n    return NULL;\n  }\n  __CPROVER_assert(c < 0x80, \"vim_strchr: ASCII branch\");\n"
       "  return (char *)strchr(string, c);\n}\n"
       "static int utfc_ptr2len(const char *const p)\n{\n" + FAST_UC +
       "  __CPROVER_assert(0, \"utfc_ptr2len: non-ASCII path reached\");\n  return 1;\n}\n"
       "static int utf_head_off(const char *base_in, const char *p_in)\n{\n" + FAST_UH +
       "  __CPROVER_assert(0, \"utf_head_off: non-ASCII path reached\");\n  return 0;\n}\n")
open(sys.argv[2], "w").write(pre + "".join(parts))
