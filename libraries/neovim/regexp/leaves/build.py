"""Standalone C file with the exact text of 8 small regexp.c functions.

Usage: python3 -I build.py <neovim checkout> <out.c>
Pieces are pinned by sha256 (tools/extract_c.py); any change stops the build.
The same text is in upstream 7b87ce8 and the fixed fork.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools"))
from extract_c import build

PRELUDE = """\
// Prelude: the regexp.c / ascii_defs.h macros and declarations these functions use.
#include <stdbool.h>
#include <stdint.h>
#define FUNC_ATTR_NONNULL_ALL
#define BS              '\\010'
#define TAB             '\\011'
#define CAR             '\\015'  // CR is used by Mac OS X
#define ESC             '\\033'
#define Magic(x)        ((int)(x) - 256)
#define un_Magic(x)     ((x) + 256)
#define is_Magic(x)     ((x) < 0)
#define NOT_MULTI       0
#define MULTI_ONE       1
#define MULTI_MULT      2
#define RF_HASNL    4   // can match a NL
#define OPERAND_MIN(p)  (((int64_t)(p)[3] << 24) + ((int64_t)(p)[4] << 16) \\
                         + ((int64_t)(p)[5] << 8) + (int64_t)(p)[6])
#define OPERAND_CMP(p)  (p)[7]
typedef struct regengine regengine_T;   // opaque here: never dereferenced
typedef struct regprog regprog_T;
struct regprog {
  regengine_T *engine;
  unsigned regflags;
  unsigned re_engine;  ///< Automatic, backtracking or NFA engine.
  unsigned re_flags;   ///< Second argument for vim_regcomp().
  bool re_in_use;      ///< prog is being executed
};
static int had_eol;             ///< true when EOL found by vim_regcomp()
"""
R = "src/nvim/regexp.c"
CHECKS = [
    ("src/nvim/ascii_defs.h", "#define BS              '\\010'"),
    ("src/nvim/ascii_defs.h", "#define TAB             '\\011'"),
    ("src/nvim/ascii_defs.h", "#define CAR             '\\015'  // CR is used by Mac OS X"),
    ("src/nvim/ascii_defs.h", "#define ESC             '\\033'"),
    (R, "#define Magic(x)        ((int)(x) - 256)"),
    (R, "#define un_Magic(x)     ((x) + 256)"),
    (R, "#define is_Magic(x)     ((x) < 0)"),
    (R, "#define NOT_MULTI       0"),
    (R, "#define MULTI_ONE       1"),
    (R, "#define MULTI_MULT      2"),
    (R, "#define RF_HASNL    4   // can match a NL"),
    (R, "#define OPERAND_MIN(p)  (((int64_t)(p)[3] << 24) + ((int64_t)(p)[4] << 16) \\"),
    (R, "                         + ((int64_t)(p)[5] << 8) + (int64_t)(p)[6])"),
    (R, "#define OPERAND_CMP(p)  (p)[7]"),
    ("src/nvim/types_defs.h", "typedef struct regprog regprog_T;"),
    (R, "struct regprog {"),
    (R, "  regengine_T *engine;"),
    (R, "  unsigned regflags;"),
    (R, "  unsigned re_engine;  ///< Automatic, backtracking or NFA engine."),
    (R, "  unsigned re_flags;   ///< Second argument for vim_regcomp()."),
    (R, "  bool re_in_use;      ///< prog is being executed"),
    (R, "static int had_eol;             ///< true when EOL found by vim_regcomp()"),
]
PIECES = [
    (R, "no_Magic", "91829aff4cd877f26948ec685d68dd8e7ee69f9338f729e17851932041e2c703"),
    (R, "toggle_Magic", "7303e5278d26e85c7118769ba5d46af86735ef270841574c403bc2b174fa37ed"),
    (R, "re_multi_type", "b674838c8bb983b98a9501b9ca4be4ab0d96213b9d94338aee49653d6a7efca7"),
    (R, "backslash_trans", "07e6666d5a0fa8bdd9b6bb2d83d777caf11437650b61edeb59301ca05a641d84"),
    (R, "re_multiline", "49d153b46917b3c65e22363e576e8934b4a4999b9b2df62dcf6f56ce7104a661"),
    (R, "vim_regcomp_had_eol", "e60f30cab134a397800e905f8e661c5b9a2f6dcbabf02ad56a7bb0d3b618f566"),
    (R, "re_num_cmp", "59b18521c04958fee492e00130758a9716218dd4657fafba0bd0da5505120cf2"),
    (R, "nfa_re_num_cmp", "a5deb50d54aa481554bd6e5c33553bbd3ac373e6850eabb68358ab02f3d384aa"),
]

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], PRELUDE, CHECKS, PIECES)
