"""Round 2: standalone C file with exact upstream text for more mbyte.c helpers.
Usage: python3 -I build.py <neovim checkout> <out.c>. Pieces are sha256-pinned on first run (PINS)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cbmc"))
import extract as X
X.SPECIAL["utf8len_tab_zero"] = ("src/nvim/mbyte.c", r"^const uint8_t utf8len_tab_zero\[\] = \{$", r"^\};$")
NAMES = ["utf8len_tab", "utf8len_tab_zero", "utf_ptr2char", "utf_ptr2len", "utf_ptr2CharInfo_impl",
         "utf_safe_read_char_adv", "mb_cptr2char_adv"]
PINS = {}
pf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pins.txt")
if os.path.exists(pf):
    PINS = dict(l.split() for l in open(pf) if l.strip())
def main(tree, out):
    got = X.extract(tree, NAMES)
    parts = [X.PRELUDE]
    for n in NAMES:
        where, piece, h = got[n]
        if PINS and PINS.get(n) != h:
            sys.exit(f"build: {n} ({where}) changed: sha256 {h}")
        parts.append(f"// {where} (verbatim)\n{piece}\n")
    open(out, "w").write("\n".join(parts))
    if not PINS:
        open(pf, "w").write("".join(f"{n} {got[n][2]}\n" for n in NAMES))
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
