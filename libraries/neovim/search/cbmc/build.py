"""Standalone C file with the exact text of search.c's set_last_csearch.

Usage: python3 -I build.py <neovim checkout> <out.c>
Prints "fixed" or "upstream" for the version found. Pieces are pinned by
sha256 (tools/extract_c.py); any other text stops the build.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools"))
from extract_c import build

PRELUDE = """\
// Prelude: the macros and globals of search.c that set_last_csearch uses.
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#define FUNC_ATTR_CONST
#define FUNC_ATTR_ALWAYS_INLINE
#define NUL '\\0'
#define MAX_SCHAR_SIZE 32
#define CLEAR_FIELD(field)  memset(&(field), 0, sizeof(field))
static uint8_t lastc[2] = { NUL, NUL };   // last character searched for
static char lastc_bytes[MAX_SCHAR_SIZE + 1];
static int lastc_bytelen = 1;             // >1 for multi-byte char
"""
CHECKS = [
    ("src/nvim/types_defs.h", "#define MAX_SCHAR_SIZE 32"),
    ("src/nvim/memory.h", "#define CLEAR_FIELD(field)  memset(&(field), 0, sizeof(field))"),
    ("src/nvim/search.c", "static uint8_t lastc[2] = { NUL, NUL };   // last character searched for"),
    ("src/nvim/search.c", "static char lastc_bytes[MAX_SCHAR_SIZE + 1];"),
    ("src/nvim/search.c", "static int lastc_bytelen = 1;             // >1 for multi-byte char"),
]
TRAIL = ("src/nvim/mbyte.h", "utf_is_trail_byte", "321508ca96f615cc650d1f834d7dd45c0ba2f789e2bf1d8c06d0bc2b21f4c561")
UPSTREAM = "0c27c12c39090e7bcfd30c7e5670174952d8ff815da05202e31f49ec15ff6e28"
FIXED = "c898942f43d49a99fc53b32c01e32512501d469074117468a176f3245ad9de2e"

if __name__ == "__main__":
    tree, out = sys.argv[1], sys.argv[2]
    try:
        build(tree, out, PRELUDE, CHECKS, [TRAIL, ("src/nvim/search.c", "set_last_csearch", FIXED)])
        print("fixed")
    except SystemExit:
        build(tree, out, PRELUDE, CHECKS, [TRAIL, ("src/nvim/search.c", "set_last_csearch", UPSTREAM)])
        print("upstream")
