#!/usr/bin/env python3
"""Extract grid.c functions (and mbyte.c's utf_char2bytes) verbatim, check sha256 pins.
Usage: build.py <neovim checkout> <out.c>"""
import hashlib, re, sys
NV, OUT = sys.argv[1], sys.argv[2]
# name -> (file, sha256 of the extracted text at upstream 7b87ce8)
FUNCS = [
    ("utf_char2bytes", "src/nvim/mbyte.c"),
    ("schar_high", "src/nvim/grid.c"),
    ("schar_get_adv", "src/nvim/grid.c"),
    ("schar_get", "src/nvim/grid.c"),
    ("schar_len", "src/nvim/grid.c"),
    ("schar_get_first_byte", "src/nvim/grid.c"),
    ("schar_get_ascii", "src/nvim/grid.c"),
    ("schar_in_arabic_block", "src/nvim/grid.c"),
    ("schar_from_char", "src/nvim/grid.c"),
    ("grid_adjust", "src/nvim/grid.c"),
    ("grid_invalid_row", "src/nvim/grid.c"),
    ("grid_getchar", "src/nvim/grid.c"),
    ("grid_line_getchar", "src/nvim/grid.c"),
    ("grid_line_put_schar", "src/nvim/grid.c"),
]
PINS = {}
try:
    for line in open(__file__.rsplit("/", 1)[0] + "/pins.txt"):
        n, h = line.split(); PINS[n] = h
except FileNotFoundError:
    pass
def extract(src, name):
    m = re.search(r"^[^\n;{}]*\b" + name + r"\(([^)]*)\)\n(?:  FUNC_ATTR[^\n]*\n)*\{", src, re.M)
    if not m: sys.exit(f"{name}: not found")
    i, depth = m.end() - 1, 0
    for j in range(i, len(src)):
        if src[j] == "{": depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0: break
    text = src[m.start():j + 1]
    return re.sub(r"\n  FUNC_ATTR[^\n]*", "", text)
out, newpins, bad = [], [], False
# grid.c's little-endian schar_idx macro, copied verbatim; fail if upstream changed it.
MACRO = "# define schar_idx(sc) (sc >> 8)"
if MACRO not in open(f"{NV}/src/nvim/grid.c").read(): sys.exit("schar_idx macro changed")
out.append(MACRO.replace("# define", "#define"))
# grid_line_* state (static globals), copied verbatim as one block.
_g = open(f"{NV}/src/nvim/grid.c").read()
_i = _g.index("static ScreenGrid *grid_line_grid = NULL;"); _j = _g.index("static int grid_line_flags = 0;") + len("static int grid_line_flags = 0;")
out.append(_g[_i:_j]); newpins.append("grid_line_state " + hashlib.sha256(_g[_i:_j].encode()).hexdigest())
if PINS and PINS.get("grid_line_state") != hashlib.sha256(_g[_i:_j].encode()).hexdigest() and "grid_line_state" not in sys.argv[3:]:
    print("grid_line_state differs from pin", file=sys.stderr); bad = True
for name, f in FUNCS:
    t = extract(open(f"{NV}/{f}").read(), name)
    h = hashlib.sha256(t.encode()).hexdigest()
    newpins.append(f"{name} {h}")
    if PINS and PINS.get(name) != h and name not in sys.argv[3:]:
        print(f"{name}: sha256 {h} differs from pin", file=sys.stderr); bad = True
    out.append(t)
if not PINS: print("\n".join(newpins))
open(OUT, "w").write("\n\n".join(out) + "\n")
sys.exit(1 if bad else 0)
