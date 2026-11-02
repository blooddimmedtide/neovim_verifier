"""Write a standalone C file holding exact upstream text from src/nvim/mbyte.c.

Usage: python3 -I build.py <neovim checkout> <out.c>
Each piece is checked against the sha256 recorded below; any upstream change
stops the build until the piece is reviewed again.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract import PRELUDE, extract

REVIEWED = {
    "CharBoundsOff": "06599a99ba18835b648a020b61a8d0680c509519ec1b3b2431d6dba9d1f8f141",
    "utf_is_trail_byte": "321508ca96f615cc650d1f834d7dd45c0ba2f789e2bf1d8c06d0bc2b21f4c561",
    "utf8len_tab": "dc55b48018295f808d07d932176af8edf225e51808089abf86da683fcc16a342",
    "utf_ptr2char": "6962b990c458e23a01f29cf2f18e9058a16eda84bdb4445016cfc22d74e7bbd6",
    "utf_ptr2len": "d1342b369ed23c9e609ad64662cc17cb7d0aecd6a8a924c3fa7cdf7f2d0e8aab",
    "utf_byte2len": "1d8f2fb181840038b59165e4128dbbc3a40ba7977bbc030df1803db9b2265d75",
    "utf_ptr2len_len": "175e6a9f012bc0afcb1c2faad9484a991578928234c88dde8ad950f2f14ae807",
    "utf_char2len": "3cf444d6a6583cccded1ebfbc631072a04e2ad7cc1c48daf3142802d223a6269",
    "utf_char2bytes": "912fa872a6f92cf89173e88127394ac878b206ae12ef9d599b1134aeb1513617",
    "utf_cp_bounds_len": "725562d65073c4b2b5d59abdce4955f66e9896732786babbeaef473be47b20af",
    "utf_cp_bounds": "815dfe036339e5611eaf4554a1d6e1a0c4f062d7a7f06e2c257f1be46d653b6c",
}

# Fixed versions in blooddimmedtide/verified_neovim (findings/). A fixed piece
# also defines a macro so the harness drops the upstream-only precondition.
FIXED = {
    "utf_cp_bounds_len": ("4b347b3d3b9b0ad5cf12a3026957ad68d3af961eb8a7e6b11a2a6f1deb1fe8ed", "NVIM_FIXED_CP_BOUNDS"),
}

def main(tree, out):
    got = extract(tree, list(REVIEWED))
    parts = [PRELUDE]
    for name, want in REVIEWED.items():
        where, piece, h = got[name]
        if name in FIXED and h == FIXED[name][0]:
            parts.append(f"#define {FIXED[name][1]} 1  // fixed fork version")
        elif h != want:
            sys.exit(f"build: {name} ({where}) changed upstream: sha256 {h}")
        parts.append(f"// {where} (verbatim)\n{piece}\n")
    open(out, "w").write("\n".join(parts))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
