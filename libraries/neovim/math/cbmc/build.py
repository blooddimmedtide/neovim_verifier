"""Standalone copy of src/nvim/math.c's functions (exact text, sha256 pinned).
Usage: python3 -I build.py <neovim checkout> <out.c> [--fallback]
--fallback undefines __GNUC__/__clang__ after the system headers, so xctz and
xpopcount use their portable loops (what non-GCC/Clang compilers build).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools"))
from extract_c import build

F = "src/nvim/math.c"
PIECES = [
    (F, "xfpclassify", "0e656b5b80643edf07e8adfe1f551c8a2ed3c4b1b137dc4ef98f82f82d8c5d35"),
    (F, "xisinf", "60847a99c91234f5f2d2e3874d011af8b216c4da145ba3cda9014219697ff6a3"),
    (F, "xisnan", "90049913b2cde0d426f01b8e6a202e6539b20368e7f48400abd1dbd29fe2b54d"),
    (F, "xctz", "e46081f6cd76c702cd597ab6cddbb98a515b34eb4504a357b2981bbe87eeef32"),
    (F, "xpopcount", "0287be065f798cf37eb6a8d0d1845eda57884cc769f115610cd4a7654763863b"),
    (F, "vim_append_digit_int", "afa9148ed0afb8dcbdd13bc1d417e50cf7cccab7cf7b31cc9bb369ffccf6d797"),
    (F, "trim_to_int", "bcaace86bcb3d24883eab6cccf0c0ee3418053caa68cfbb260469683fcf9ddde"),
]
CHECKS = [("src/nvim/vim_defs.h", "# define OK                     1"),
          ("src/nvim/vim_defs.h", "#define FAIL                    0"),
          (F, "#include <math.h>"), (F, "#include <limits.h>"), (F, "#include <string.h>")]
PRELUDE = """\
// Prelude: math.c's own system headers, Neovim's OK/FAIL, FUNC_ATTR_* as nothing.
#include <math.h>
#include <limits.h>
#include <stdint.h>
#include <string.h>
#define OK 1
#define FAIL 0
#define FUNC_ATTR_CONST
"""

if __name__ == "__main__":
    pre = PRELUDE + ("#undef __GNUC__\n#undef __clang__\n" if "--fallback" in sys.argv else "")
    build(sys.argv[1], sys.argv[2], pre, CHECKS, PIECES)
