"""Round 2: standalone C file with exact upstream text for more mbyte.c helpers.
Usage: python3 -I build.py <neovim checkout> <out.c>. Pieces are sha256-pinned on first run (PINS)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cbmc"))
import extract as X
X.SPECIAL["utf_ptr2CharInfo_len"] = ("src/nvim/mbyte.h", r"^static inline CharInfo utf_ptr2CharInfo_len\(", r"^\}$")
X.SPECIAL["utf8len_tab_zero"] = ("src/nvim/mbyte.c", r"^const uint8_t utf8len_tab_zero\[\] = \{$", r"^\};$")
NAMES = ["utf8len_tab", "utf8len_tab_zero", "utf_ptr2char", "utf_ptr2len", "utf_ptr2CharInfo_impl",
         "utf_safe_read_char_adv", "mb_cptr2char_adv", "utf_ptr2CharInfo_len"]
PINS = {}
# Fixed pieces in blooddimmedtide/verified_neovim (findings/): accepted in place of the upstream pin.
FIXED = {"utf_safe_read_char_adv": "37f9bab7211067df1284a240dce11f5c84d4f2f381a7056e617c023a0431d2bf"}
pf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pins.txt")
if os.path.exists(pf):
    PINS = dict(l.split() for l in open(pf) if l.strip())
def main(tree, out):
    got = X.extract(tree, NAMES)
    parts = [X.PRELUDE, "// CharInfo as in src/nvim/mbyte_defs.h:61-64\ntypedef struct {\n  int32_t value;\n  int len;\n} CharInfo;\n"]
    for n in NAMES:
        where, piece, h = got[n]
        if PINS and PINS.get(n) != h and FIXED.get(n) != h:
            sys.exit(f"build: {n} ({where}) changed: sha256 {h}")
        parts.append(f"// {where} (verbatim)\n{piece}\n")
    open(out, "w").write("\n".join(parts))
    if not PINS:
        open(pf, "w").write("".join(f"{n} {got[n][2]}\n" for n in NAMES))
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
