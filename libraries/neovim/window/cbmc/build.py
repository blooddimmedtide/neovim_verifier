"""Standalone copy of window-size arithmetic from src/nvim/window.c (exact text, sha256 pinned).
Usage: python3 -I build.py <neovim checkout> <out.c>
The prelude declares only the struct fields these functions read or write, with
their upstream types (each checked against buffer_defs.h below).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools"))
from extract_c import build

F = "src/nvim/window.c"
B = "src/nvim/buffer_defs.h"
PIECES = [
    (F, "win_default_scroll", "4147777dbc9483182e6ccf122b5d4418483d70a7fd5a70f59f09ce9b4d3a3aff"),
    (F, "set_fraction", "978d342344e71b071199a0f8d36de3bc948a4c1dcbb2b8eb2e6373433ec4ca49"),
    (F, "frame_check_height", "753bb2e870a8a2bb79c5d93419eab6022213cedc6cf7e0be6d0e9ddc973ccbb6"),
    (F, "frame_check_width", "1b14f67585121090550c0bd36e0c5f5975914556114cb46706f7c12a4cef97bb"),
    (F, "global_stl_height", "738ce9a20d7bc94f6ed3542d40b69768d455f5ee23ffcb1de13ecfae268e0a00"),
]
CHECKS = [
    (F, "#define FRACTION_MULT   16384"),
    ("src/nvim/window.h", "  STATUS_HEIGHT = 1,  ///< height of a status line under a window"),
    ("src/nvim/types_defs.h", "typedef int64_t OptInt;"),
    ("src/nvim/option_vars.h", "EXTERN OptInt p_ls;             ///< 'laststatus'"),
    ("src/nvim/macros_defs.h", "# define MAX(X, Y) ((X) > (Y) ? (X) : (Y))"),
    ("src/nvim/globals.h", "#define FOR_ALL_FRAMES(frp, first_frame) \\"),
    ("src/nvim/globals.h", "  for ((frp) = first_frame; (frp) != NULL; (frp) = (frp)->fr_next)"),
    (B, "  char fr_layout;               // FR_LEAF, FR_COL or FR_ROW"),
    (B, "  int fr_width;"), (B, "  int fr_height;"),
    (B, "  frame_T *fr_next;         // frame right or below in same parent, NULL"),
    (B, "  frame_T *fr_child;        // first contained frame"),
    (B, "#define FR_LEAF 0       // frame is a leaf"),
    (B, "#define FR_ROW  1       // frame with a row of windows"),
    (B, "#define FR_COL  2       // frame with a column of windows"),
    (B, "  int w_view_height;"), (B, "  int w_wrow, w_wcol;               // cursor position in window"),
    (B, "  int w_fraction;"),
]
PRELUDE = """\
// Prelude: the types, fields and macros these functions use, copied from upstream (checked).
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
typedef int64_t OptInt;
typedef struct frame_S frame_T;
struct frame_S { char fr_layout; int fr_width; int fr_height; frame_T *fr_next; frame_T *fr_child; };
#define FR_LEAF 0
#define FR_ROW  1
#define FR_COL  2
typedef struct { int w_view_height; int w_wrow, w_wcol; int w_fraction; } win_T;
enum { STATUS_HEIGHT = 1 };
#define FRACTION_MULT   16384
#define MAX(X, Y) ((X) > (Y) ? (X) : (Y))
#define FOR_ALL_FRAMES(frp, first_frame) \\
  for ((frp) = first_frame; (frp) != NULL; (frp) = (frp)->fr_next)
#define FUNC_ATTR_PURE
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_NONNULL_ALL
OptInt p_ls;
"""

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], PRELUDE, CHECKS, PIECES)
