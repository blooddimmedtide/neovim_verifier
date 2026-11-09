"""CBMC copy of find_special_key for the INT_MIN property (findings/keycodes-char-int-min.md).

Usage: python3 -I build.py <neovim tree> <out dir with kt.c from ../table> <out.c>
Appends to kt.c the verbatim tables and functions find_special_key needs from keycodes.c.
One tool patch: simplify_key is renamed vp_real_simplify_key so the harness can check its
argument and then call it. Callees outside keycodes.c are harness stubs (see harness.c).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools"))
from extract_c import find
tree, kt, out = sys.argv[1:4]
lines = open(f"{tree}/src/nvim/keycodes.c").read().split("\n")
def block(first):
    s = lines.index(first); e = s
    while lines[e] != "};": e += 1
    return "\n".join(lines[s:e + 1])
def fn(name):
    s, e = find(lines, name); return "\n".join(lines[s:e + 1])
parts = [open(f"{kt}/kt.c").read(), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stubs.h")).read(),
         "#define MOD_KEYS_ENTRY_SIZE 5",
         block("const struct modmasktable mod_mask_table[] = {"), block("static uint8_t modifier_keys_table[] = {"),
         fn("name_to_mod_mask"), fn("handle_x_keys"),
         fn("simplify_key").replace("int simplify_key(", "int vp_real_simplify_key(", 1),
         "static int extract_modifiers(int key, int *modp, const bool simplify, bool *const did_simplify);",
         fn("find_special_key"), fn("extract_modifiers")]
open(out, "w").write("\n\n".join(parts) + "\n")
