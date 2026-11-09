"""Standalone copy of src/nvim/indent.c's tabstop helpers (exact text, sha256 pinned).
Usage: python3 -I build.py <neovim checkout> <out.c>
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools"))
from extract_c import build

F = "src/nvim/indent.c"
PIECES = [
    (F, "tabstop_padding", "136158640418bcab5b159b0b00e7446e08d6e7b31f8eca5635465ac7cf4c20c7"),
    (F, "tabstop_at", "a0c69a8b0fbe5aa7f8f7e39a20fa2ad51243c352d7b2f33ba3aaf618deb060eb"),
    (F, "tabstop_start", "b0467a4f23f64c77c15c2b2836bda33ccfcd7a35fc571b2ac4e81365782bcd5c"),
    (F, "tabstop_fromto", "01d0d01da8c5d5fd5c87626c6d1a65e3dd3c9b909a9164056598498917eb5a42"),
    (F, "tabstop_count", "be69a17e5e83fb8ba093f0f20e6d140304dcc176b88e463d2819a9db85e6193a"),
    (F, "tabstop_first", "6a9c2ec7e3fedcdd5e99c2d013fd78b5f26e2f9e160cb92563629df425cea7c6"),
]
CHECKS = [("src/nvim/pos_defs.h", "typedef int colnr_T;"),
          ("src/nvim/types_defs.h", "typedef int64_t OptInt;"),
          ("src/nvim/option_vars.h", "#define TABSTOP_MAX 9999")]
PRELUDE = """\
// Prelude: colnr_T/OptInt as in pos_defs.h/types_defs.h, curbuf reduced to its 'tabstop'
// field (the only one tabstop_fromto reads), FUNC_ATTR_* as nothing.
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
typedef int colnr_T;
typedef int64_t OptInt;
#define TABSTOP_MAX 9999
typedef struct { OptInt b_p_ts; } buf_T;
buf_T *curbuf;
#define FUNC_ATTR_PURE
"""

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], PRELUDE, CHECKS, PIECES)
