"""Standalone C file with exact text of regexp.c's gethexchrs and getoctchrs.

Usage: python3 -I build.py <neovim checkout> <out.c>
Pieces are pinned by sha256 (tools/extract_c.py); any change stops the build.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools"))
from extract_c import build

PRELUDE = """\
// Prelude: regexp.c's globals used here, and FUNC_ATTR_* as nothing.
#include <stdbool.h>
#include <stdint.h>
#define FUNC_ATTR_CONST
#define FUNC_ATTR_ALWAYS_INLINE
static char *regparse;          ///< Input-scan pointer.
"""
CHECKS = [("src/nvim/regexp.c", "static char *regparse;          ///< Input-scan pointer.")]
PIECES = [
    ("src/nvim/ascii_defs.h", "ascii_isxdigit", "dbbf1e2ae448d64b9d4d1378f96d2644f3043c0dc06dca16b54b1075b38aadb8"),
    ("src/nvim/charset.c", "hex2nr", "d66d66c0b78f77634dfccc6519360b2f5f339bed097b061f7a577c265a1a058f"),
    ("src/nvim/regexp.c", "gethexchrs", "245d51faa7b04895c978cdf4c48fe043f5925c4fc85f6899e82f7c843a4144cf"),
    ("src/nvim/regexp.c", "getoctchrs", "0f03a7706e39b2f46748d583f766c8ce52a1af2ce77443e3698d3737e3043c5c"),
]

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], PRELUDE, CHECKS, PIECES)
