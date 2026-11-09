"""Annotated standalone copy of the typeahead/stuff buffer functions of src/nvim/input.c.

Usage: python3 -I build.py <neovim checkout> <out.c> [upstream|fixed]
Each function is the exact upstream (or fixed-fork) text, sha256 pinned. ACSL is
inserted as comments only; removing every /*@ ... */ must give the source back.
The prelude copies the types and macros the functions use; build.py checks each
copied line against the upstream headers.
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import LOGIC, contracts, annotations

F = "src/nvim/input.c"
SHA = {  # upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
    "free_buff": "8ca4a911a2de2bd741eee63fbecb61bbc6d722b9ed18dedc4d470159eff14f5b",
    "add_buff": "1eb507e6d3345aec5ac46e21e46005c2466b37bce1ada6133b8455083aca3b74",
    "read_readbuf": "45eb0d06ebfef7e985d2c55b8831e3cf0c89484af3c6459f3f0280fae46c9182",
    "read_readbuffers": "6b5b487d206d1c9127d22530b611e12abcba293aab77a148ae679c37e745f9f7",
    "start_stuff": "6736f8fe3f0b6668326b82ad423403c3e37705b219ebf0db2658719610b4760f",
    "stuff_empty": "03c68d43b8b0edc166e578509dde39251f68f547acc9aeb65bf0b124ec6dfe7c",
    "readbuf1_empty": "22d1a77e72ad6b964b2c9a12d1c2b4f8537d9cdde11b9240a03808efda522715",
    "init_typebuf": "9fa3c69bc3ed6fc7c57655816e802f432631f3fc05d7ec80b61f07cd914cee3f",
    "ins_typebuf": "900e703766a0da705191a1d0444bd7c297379254a074ac0e311fd398311c73ff",
    "typebuf_changed": "aadc7c39ecb4a39654d406878af572cb2e49dd7250388af5019bca65a0d59e95",
    "typebuf_typed": "42d340d205f3439e6f8252a039d346f36c5c4596d910ed2e8b99811159b0335d",
    "typebuf_maplen": "b2d44d8b73759b93d726350a126b23712cc7a04d68ca18b63d49e2a25adb0d95",
    "del_typebuf": "34104e20b166ba848bd782e066f071484f5a7801f93766ddf9d9018fe81ab4b0",
    "alloc_typebuf": "b3c28adc74c54c5103ebbb0db37268c33389b119dcc45e13f2454b0462e9b889",
    "free_typebuf": "27c8bdb032ebc672f6cfe15c56319ea90123d6924c75813c59a2d7110e3b33d2",
    "put_string_in_typebuf": "39d099d87128a8190f3adb4023c4348fd26c7f0832655763e658b0bf7b9b098c",
}
FIXED_SHA = {}
PRELUDE = r"""
#include <limits.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include "vp_typebuf.h"
#define NUL '\000'
#define OK 1
#define FAIL 0
#define MAX(X, Y) ((X) > (Y) ? (X) : (Y))
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_PURE
#define _(x) ((char *)(x))
#define assert(e) /*@ assert e; */
enum { MAXMAPLEN = 50, };
typedef struct { size_t size; size_t capacity; char *items; } StringBuilder;
typedef struct {
  StringBuilder keys;
  size_t read;
  size_t insert;
} StuffBuf;
typedef struct {
  uint8_t *tb_buf;
  uint8_t *tb_noremap;
  int tb_buflen;
  int tb_off;
  int tb_len;
  int tb_maplen;
  int tb_silent;
  int tb_no_abbr_cnt;
  int tb_change_cnt;
} typebuf_T;
enum RemapValues { REMAP_YES = 0, REMAP_NONE = -1, REMAP_SCRIPT = -2, REMAP_SKIP = -3, };
enum { RM_YES = 0, RM_NONE = 1, RM_SCRIPT = 2, RM_ABBR = 4, };
#define TYPELEN_INIT    (5 * (MAXMAPLEN + 3))
#define kv_roundup32(x) \
  ((--(x)), \
   ((x)|=(x)>>1, (x)|=(x)>>2, (x)|=(x)>>4, (x)|=(x)>>8, (x)|=(x)>>16), \
   (++(x)))
#define kv_init(v) ((v).size = (v).capacity = 0, (v).items = 0)
#define kv_destroy(v) \
  do { \
    xfree((v).items); \
    kv_init(v); \
  } while (0)
#define kv_resize(v, s) \
  ((v).capacity = (s), \
   (v).items = xrealloc((v).items, sizeof((v).items[0]) * (v).capacity))
#define kv_ensure_space(v, len) \
  do { \
    assert((len) <= SIZE_MAX - (v).size); \
    if ((v).capacity < (v).size + (len)) { \
      (v).capacity = (v).size + (len); \
      kv_roundup32((v).capacity); \
      kv_resize((v), (v).capacity); \
    } \
  } while (0)
#define XFREE_CLEAR(ptr) \
  do { \
    void **ptr_ = (void **)&(ptr); \
    xfree(*ptr_); \
    *ptr_ = NULL; \
    (void)(*ptr_); \
  } while (0)
typebuf_T typebuf;
bool typebuf_was_filled;
bool cmd_silent;
static StuffBuf readbuf1;
static StuffBuf readbuf2;
static uint8_t typebuf_init[TYPELEN_INIT];
static uint8_t noremapbuf_init[TYPELEN_INIT];
extern const char e_command_too_complex[];
/*@ // emsg() (message.c) also flushes the typeahead: it may change typebuf and its
    // buffers. ins_typebuf returns FAIL right after; its contract says nothing about typebuf then.
    assigns typebuf, typebuf_was_filled, cmd_silent, vp_live,
            typebuf.tb_buf[0 .. typebuf.tb_buflen - 1], typebuf.tb_noremap[0 .. typebuf.tb_buflen - 1];
*/
int emsg(const char *s);
static int read_readbuf(StuffBuf *buf, bool advance);
void del_typebuf(int len, int offset);
int ins_typebuf(char *str, int noremap, int offset, bool nottyped, bool silent) /*@ ghost (size_t n) */;
"""
# (file, exact text) the prelude copies; checked against the pinned tree
CHECKS = [("src/nvim/mapping_defs.h", "enum { MAXMAPLEN = 50, };"),
          ("src/nvim/input.c", "#define TYPELEN_INIT    (5 * (MAXMAPLEN + 3))"),
          ("src/nvim/macros_defs.h", "# define MAX(X, Y) ((X) > (Y) ? (X) : (Y))"),
          ("src/nvim/ascii_defs.h", "#define NUL             '\\000'"),
          ("src/nvim/vim_defs.h", "# define OK                     1"),
          ("src/nvim/vim_defs.h", "#define FAIL                    0"),
          ("src/klib/kvec.h", "#define kv_roundup32(x) \\\n  ((--(x)), \\\n   ((x)|=(x)>>1, (x)|=(x)>>2, (x)|=(x)>>4, (x)|=(x)>>8, (x)|=(x)>>16), \\\n   (++(x)))"),
          ("src/klib/kvec.h", "#define kv_destroy(v) \\\n  do { \\\n    xfree((v).items); \\\n    kv_init(v); \\\n  } while (0)"),
          ("src/klib/kvec.h", "#define kv_init(v) ((v).size = (v).capacity = 0, (v).items = 0)"),
          ("src/klib/kvec.h", "#define kv_resize(v, s) \\\n  ((v).capacity = (s), \\\n   (v).items = xrealloc((v).items, sizeof((v).items[0]) * (v).capacity))"),
          ("src/klib/kvec.h", "#define kv_ensure_space(v, len) \\\n  do { \\\n    assert((len) <= SIZE_MAX - (v).size); \\\n    if ((v).capacity < (v).size + (len)) { \\\n      (v).capacity = (v).size + (len); \\\n      kv_roundup32((v).capacity); \\\n      kv_resize((v), (v).capacity); \\\n    } \\\n  } while (0)"),
          ("src/nvim/input_defs.h", "  StringBuilder keys;  ///< Bytes; `[read, keys.size)` is unread."),
          ("src/nvim/input_defs.h", "  size_t read;         ///< Read position: consumed up to here. Reset (keeping capacity) on drain."),
          ("src/nvim/input_defs.h", "  size_t insert;       ///< Write position: `keys.size`, or the read position as of start_stuff()"),
          ("src/nvim/input_defs.h", "  uint8_t *tb_buf;      ///< buffer for typed characters"),
          ("src/nvim/input_defs.h", "  uint8_t *tb_noremap;  ///< mapping flags for characters in tb_buf[]"),
          ("src/nvim/input_defs.h", "  int tb_buflen;        ///< size of tb_buf[]"),
          ("src/nvim/input_defs.h", "  int tb_off;           ///< current position in tb_buf[]"),
          ("src/nvim/input_defs.h", "  int tb_len;           ///< number of valid bytes in tb_buf[]"),
          ("src/nvim/input_defs.h", "  int tb_maplen;        ///< nr of mapped bytes in tb_buf[]"),
          ("src/nvim/input_defs.h", "  int tb_silent;        ///< nr of silently mapped bytes in tb_buf[]"),
          ("src/nvim/input_defs.h", "  int tb_no_abbr_cnt;   ///< nr of bytes without abbrev. in tb_buf[]"),
          ("src/nvim/input_defs.h", "  int tb_change_cnt;    ///< nr of time tb_buf was changed; never zero"),
          ("src/nvim/input_defs.h", "  REMAP_YES = 0,      ///< Allow remapping."),
          ("src/nvim/input_defs.h", "  REMAP_NONE = -1,    ///< No remapping."),
          ("src/nvim/input_defs.h", "  REMAP_SCRIPT = -2,  ///< Remap script-local mappings only."),
          ("src/nvim/input_defs.h", "  REMAP_SKIP = -3,    ///< No remapping for first char."),
          ("src/nvim/input.c", "  RM_YES    = 0,  ///< tb_noremap: remap"),
          ("src/nvim/input.c", "  RM_NONE   = 1,  ///< tb_noremap: don't remap"),
          ("src/nvim/input.c", "  RM_SCRIPT = 2,  ///< tb_noremap: remap local script mappings"),
          ("src/nvim/input.c", "  RM_ABBR   = 4,  ///< tb_noremap: don't remap, do abbrev."),
          ("src/nvim/types_defs.h", "typedef kvec_t(char) StringBuilder;"),
          ("src/klib/kvec.h", "    size_t size; \\\n    size_t capacity; \\\n    type *items; \\")]


def strip(s):
    s = re.sub(r"^[ \t]*/\*@.*?\*/\n", "", s, flags=re.S | re.M)
    s = re.sub(r" /\*@.*?\*/", "", s, flags=re.S)
    return re.sub(r"/\*@.*?\*/ ", "", s, flags=re.S)


def main(tree, out, mode="upstream"):
    fixed = mode == "fixed"
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read():
            sys.exit(f"build: {path} no longer contains: {text!r}")
    lines = open(f"{tree}/{F}").read().split("\n")
    C, A = contracts(fixed), annotations(fixed)
    parts, missing = [PRELUDE, LOGIC], False
    for name, want in SHA.items():
        if name not in C:
            print(f"build: {name}: no contract yet, left out", file=sys.stderr)
            missing = True
            continue
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        h = hashlib.sha256(piece.encode()).hexdigest()
        if fixed and name in FIXED_SHA:
            want = FIXED_SHA[name]
        if h != want:
            sys.exit(f"build: {name} ({F}:{s + 1}) differs from the pinned {mode} text: sha256 {h}")
        annotated = piece
        for kind, anchor, annot in A.get(name, []):
            if annotated.count(anchor) != 1:
                sys.exit(f"build: {name}: anchor not found once: {anchor!r}")
            if kind == "before":
                indent = re.match(r"\s*", anchor).group(0)
                annotated = annotated.replace(anchor, f"{indent}/*@ {annot} */\n{anchor}")
            elif kind == "after":
                annotated = annotated.replace(anchor, f"{anchor} /*@ {annot} */")
            elif kind == "inline":
                annotated = annotated.replace(anchor, f"/*@ {annot} */ {anchor}")
            else:
                sys.exit(f"build: bad annotation kind {kind}")
        if strip(annotated) != piece:
            sys.exit(f"build: {name}: stripping the annotations does not give the source back")
        parts.append(f"// {F}:{s + 1} ({mode}, verbatim plus ACSL comments)\n/*@ {C[name]} */\n{annotated}\n")
    open(out, "w").write("\n".join(parts))
    if missing:
        sys.exit(2)


if __name__ == "__main__":
    main(*sys.argv[1:])
