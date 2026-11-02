"""Standalone C file with the exact text of search.c's set_last_csearch and the
small accessors of search.c's state (see harness.c).

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
#define FUNC_ATTR_PURE
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define NUL '\\0'
#define MAX_SCHAR_SIZE 32
#define CLEAR_FIELD(field)  memset(&(field), 0, sizeof(field))
static uint8_t lastc[2] = { NUL, NUL };   // last character searched for
static char lastc_bytes[MAX_SCHAR_SIZE + 1];
static int lastc_bytelen = 1;             // >1 for multi-byte char
// Types, copied line by line from the headers (field lines checked below).
typedef int32_t linenr_T;
typedef int colnr_T;
typedef uint64_t Timestamp;
typedef struct { int dummy; } AdditionalData;   // opaque here: never dereferenced
typedef struct regprog regprog_T;
enum { NSUBEXP = 10 };
typedef enum {
  kDirectionNotSet = 0,
  FORWARD = 1,
  BACKWARD = -1,
  FORWARD_FILE = 3,
  BACKWARD_FILE = -3,
} Direction;
enum {
  RE_SEARCH = 0,  ///< save/use pat in/from search_pattern
  RE_SUBST  = 1,  ///< save/use pat in/from subst_pattern
  RE_BOTH   = 2,  ///< save pat in both patterns
  RE_LAST   = 2,  ///< use last used pattern if "pat" is NULL
};
typedef struct {
  linenr_T lnum;        ///< line number
  colnr_T col;          ///< column number
} lpos_T;
typedef struct {
  regprog_T *regprog;
  lpos_T startpos[NSUBEXP];
  lpos_T endpos[NSUBEXP];
} regmmatch_T;   // trailing fields left out: not used by first_submatch
typedef struct {
  char dir;     ///< Search direction: forward ('/') or backward ('?')
  bool line;    ///< True if search has line offset.
  bool end;     ///< True if search sets cursor at the end.
  int64_t off;  ///< Actual offset value.
} SearchOffset;
typedef struct {
  char *pat;            ///< The pattern (in allocated memory) or NULL.
  size_t patlen;        ///< The length of the pattern (0 if pat is NULL).
  bool magic;           ///< Magicness of the pattern.
  bool no_scs;          ///< No smartcase for this pattern.
  Timestamp timestamp;  ///< Time of the last change.
  SearchOffset off;     ///< Pattern offset.
  AdditionalData *additional_data;  ///< Additional data from ShaDa file.
} SearchPattern;
static SearchPattern spats[2];
static int last_idx = 0;        // index in spats[] for RE_LAST
static Direction lastcdir = FORWARD;      // last direction of character search
static bool last_t_cmd = true;            // last search t_cmd
static char *mr_pattern = NULL;
"""
CHECKS = [
    ("src/nvim/types_defs.h", "#define MAX_SCHAR_SIZE 32"),
    ("src/nvim/memory.h", "#define CLEAR_FIELD(field)  memset(&(field), 0, sizeof(field))"),
    ("src/nvim/search.c", "static uint8_t lastc[2] = { NUL, NUL };   // last character searched for"),
    ("src/nvim/search.c", "static char lastc_bytes[MAX_SCHAR_SIZE + 1];"),
    ("src/nvim/search.c", "static int lastc_bytelen = 1;             // >1 for multi-byte char"),
    ("src/nvim/pos_defs.h", "typedef int32_t linenr_T;"),
    ("src/nvim/pos_defs.h", "typedef int colnr_T;"),
    ("src/nvim/os/time_defs.h", "typedef uint64_t Timestamp;"),
    ("src/nvim/types_defs.h", "typedef struct regprog regprog_T;"),
    ("src/nvim/regexp_defs.h", "  NSUBEXP = 10,"),
    ("src/nvim/regexp_defs.h", "  regprog_T *regprog;"),
    ("src/nvim/regexp_defs.h", "  lpos_T startpos[NSUBEXP];"),
    ("src/nvim/regexp_defs.h", "  lpos_T endpos[NSUBEXP];"),
    ("src/nvim/regexp_defs.h", "} regmmatch_T;"),
    ("src/nvim/vim_defs.h", "  kDirectionNotSet = 0,"),
    ("src/nvim/vim_defs.h", "  FORWARD = 1,"),
    ("src/nvim/vim_defs.h", "  BACKWARD = -1,"),
    ("src/nvim/vim_defs.h", "  FORWARD_FILE = 3,"),
    ("src/nvim/vim_defs.h", "  BACKWARD_FILE = -3,"),
    ("src/nvim/vim_defs.h", "} Direction;"),
    ("src/nvim/search.h", "  RE_SEARCH = 0,  ///< save/use pat in/from search_pattern"),
    ("src/nvim/search.h", "  RE_SUBST  = 1,  ///< save/use pat in/from subst_pattern"),
    ("src/nvim/pos_defs.h", "  linenr_T lnum;        ///< line number"),
    ("src/nvim/pos_defs.h", "  colnr_T col;          ///< column number"),
    ("src/nvim/pos_defs.h", "} lpos_T;"),
    ("src/nvim/search.h", "  char dir;     ///< Search direction: forward ('/') or backward ('?')"),
    ("src/nvim/search.h", "  int64_t off;  ///< Actual offset value."),
    ("src/nvim/search.h", "} SearchOffset;"),
    ("src/nvim/search.h", "  char *pat;            ///< The pattern (in allocated memory) or NULL."),
    ("src/nvim/search.h", "  size_t patlen;        ///< The length of the pattern (0 if pat is NULL)."),
    ("src/nvim/search.h", "  SearchOffset off;     ///< Pattern offset."),
    ("src/nvim/search.h", "} SearchPattern;"),
    ("src/nvim/search.c", "static SearchPattern spats[2] = {"),
    ("src/nvim/search.c", "static int last_idx = 0;        // index in spats[] for RE_LAST"),
    ("src/nvim/search.c", "static Direction lastcdir = FORWARD;      // last direction of character search"),
    ("src/nvim/search.c", "static bool last_t_cmd = true;            // last search t_cmd"),
    ("src/nvim/search.c", "static char *mr_pattern = NULL;"),
]
S = "src/nvim/search.c"
ACCESSORS = [
    (S, "get_search_pat", "559af6e3110984536cf5f34240e7028462f2cab6a60f022bf7671a280a0cabc3"),
    (S, "last_search_pattern", "f01a693418f59bfbbebc6b13137c82beef409882924cb4f9304262169a67e472"),
    (S, "last_search_pattern_len", "c97b6cb21ff2ddfb285113dbbfabb28cb6193759de2eaef7f28eff144eebbabe"),
    (S, "last_csearch", "57d4fe779105d1e2df5a0c4125889334bd745d321724bfaae4e2eb00a313a4c0"),
    (S, "last_csearch_forward", "4fa0014fecee7ddfb16d6188096d06152ea788788e12a9f25b53381559a2d129"),
    (S, "last_csearch_until", "f453b78dd1679ea53f38496e0a9808be4ff9c31168c557a19e26a5b72982abe3"),
    (S, "set_csearch_direction", "3a291b2684dd9aa80120c01e3633c9e89b57ad3736846d61254e2d3340ec36d7"),
    (S, "set_csearch_until", "b69f6fba3a14e4110d43bda827ef5e10cf07a8a066936aca86b10f50dfd197bd"),
    (S, "set_search_direction", "496ce17c7f80d3f7cc037908e0e2dd1cdc2dcb0acaa0d7296b8df89526b4bae5"),
    (S, "first_submatch", "af6b9747bdfccbcc81f37e0c8dcf377513952b5fc68bfacd868cb78f14f7f97c"),
    (S, "search_pattern_cleared", "6df7e69917da301e89e5a255d7fe6381bae804b34ef549b1cb1e2634c07b77d6"),
    (S, "set_last_used_pattern", "d78093a997578111400a0236d014dd76e0c96ea12952254698929f727caa457c"),
    (S, "search_was_last_used", "ffceafaea125bcdab372e7def5d472bccb3dc41da3dc1a457d94e3b52218d381"),
]
TRAIL = ("src/nvim/mbyte.h", "utf_is_trail_byte", "321508ca96f615cc650d1f834d7dd45c0ba2f789e2bf1d8c06d0bc2b21f4c561")
UPSTREAM = "0c27c12c39090e7bcfd30c7e5670174952d8ff815da05202e31f49ec15ff6e28"
FIXED = "c898942f43d49a99fc53b32c01e32512501d469074117468a176f3245ad9de2e"

if __name__ == "__main__":
    tree, out = sys.argv[1], sys.argv[2]
    try:
        build(tree, out, PRELUDE, CHECKS, [TRAIL, ("src/nvim/search.c", "set_last_csearch", FIXED)] + ACCESSORS)
        print("fixed")
    except SystemExit:
        build(tree, out, PRELUDE, CHECKS, [TRAIL, ("src/nvim/search.c", "set_last_csearch", UPSTREAM)] + ACCESSORS)
        print("upstream")
