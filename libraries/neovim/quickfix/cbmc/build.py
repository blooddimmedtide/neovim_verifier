"""Build quickfix_efm.c: verbatim errorformat code from src/nvim/quickfix.c, sha256 pinned.
Usage: python3 -I build.py <neovim tree> <out.c>"""
import hashlib, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../tools"))
from extract_c import build

tree, out = sys.argv[1], sys.argv[2]
F = "src/nvim/quickfix.c"
src = open(f"{tree}/{F}").read().split("\n")
# The fmt_pat table (not a function): copy it verbatim and pin it too.
s = src.index("static struct fmtpattern {")
e = s
while src[e] != "};":
    e += 1
table = "\n".join(src[s:e + 1])
TABLE_SHA = "50c135f6d8d66d76e33b6b70421007435a1a0312d3dd4d4d5d1c6de9f9a21ad3"
if hashlib.sha256((table + "\n").encode()).hexdigest() != TABLE_SHA:
    sys.exit("build: fmt_pat table changed upstream")
prelude = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "prelude.h")).read()
prelude += f"\n// {F}:{s + 1} (verbatim)\n{table}\n"
checks = [(F, "#define FMT_PATTERNS 14           // maximum number of % recognized"),
          (F, "  char addr[FMT_PATTERNS];    // indices of used % patterns"),
          (F, "  int conthere;                 // %> used")]
pieces = [(F, "efmpat_to_regpat", "9df5a56d8784823eaadbc9163dd581559cea1cc5f6c7c0b160c2433db0277662"),
          (F, "scanf_fmt_to_regpat", "4416f5c61cac04648bb1af8e1a400d4058e9c1a9ffbeb1e79b3042764fbcde87"),
          (F, "efm_analyze_prefix", "963274b7ea1c44a674171e94126dccd581368d003dfe029bb468c40086b917e2"),
          (F, "efm_to_regpat", "d7763648607435d74deb24b505e4ca36f42059dd7e4218cb2a42118f512cb349"),
          (F, "efm_regpat_bufsz", "42e31410c2d0e87866068669b28a0ce6c8a9a05e418078ee46bd49f08a518745"),
          (F, "efm_option_part_len", "13f906deb67809cb724d94aa6e7a10d0fbc3fde2fe77f5e4929b9345006fb2a7")]
build(tree, out, prelude, checks, pieces)
