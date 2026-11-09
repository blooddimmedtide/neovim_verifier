"""Annotated standalone copy of register.c / ops.c helpers for Frama-C WP.

Usage: python3 -I build.py <neovim checkout> <out.c> [--pin] [--fixed]
--fixed: the checkout is the verified_neovim fix branch; pieces in pins_fixed.txt replace
the upstream pins (and their FIXED contracts are used).
Every function, type and table is the exact upstream text at the pinned commit, sha256
pinned (--pin prints the hashes for review). ACSL goes only in /*@ ... */ comments placed
before a piece; build checks that stripping them gives back the verbatim pieces.
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import LOGIC, CONTRACTS, LOOPS, FIXED

# (file, kind, name-or-(first line, last line), sha256) in output order.
# kind "fn": a column-0 function; "span": lines from the first exact line to the next exact line.
PIECES = [
    ("src/nvim/normal_defs.h", "span", ("typedef enum {", "} MotionType;"),
     "aa9e4c5a2b1ac5ac0d4fe08b37e3e8ce45f7b0f5f87c2c63ebce45d28a2f5d6e"),
    ("src/nvim/api/private/defs.h", "span", ("typedef struct {", "} String;"), None),
    ("src/nvim/register_defs.h", "span", ("/// Registers:", "};"), None),
    ("src/nvim/register_defs.h", "span", ("/// Definition of one register", "} yankreg_T;"), None),
    ("src/nvim/ops.h", "span", ("/// Operator IDs; The order must correspond to opchars[] in ops.c!", "};"), None),
    ("src/nvim/ops.c", "span", ("#define OPF_LINES  1  // operator always works on lines",
                                "#define OPF_CHANGE 2  // operator changes text"), None),
    ("src/nvim/ops.c", "span", ("static const char opchars[][3] = {", "};"), None),
    ("src/nvim/normal_defs.h", "span", ("/// Arguments for Normal mode commands.", "} cmdarg_T;"), None),
    ("src/nvim/register.c", "span", ("static yankreg_T y_regs[NUM_REGISTERS] = { 0 };",
                                     "static yankreg_T y_regs[NUM_REGISTERS] = { 0 };"), None),
    ("src/nvim/register.c", "span", ("static yankreg_T *y_previous = NULL;  // ptr to last written yankreg",
                                     "static yankreg_T *y_previous = NULL;  // ptr to last written yankreg"), None),
    ("src/nvim/ascii_defs.h", "fn", "ascii_isdigit", None),
    ("src/nvim/register.h", "fn", "op_reg_index", None),
    ("src/nvim/register.h", "fn", "get_register_name", None),
    ("src/nvim/register.h", "fn", "reg_empty", None),
    ("src/nvim/ops.c", "fn", "get_op_type", None),
    ("src/nvim/ops.c", "fn", "op_on_lines", None),
    ("src/nvim/ops.c", "fn", "op_is_change", None),
    ("src/nvim/ops.c", "fn", "op_redoable", None),
    ("src/nvim/ops.c", "fn", "get_op_char", None),
    ("src/nvim/ops.c", "fn", "get_extra_op_char", None),
    ("src/nvim/ops.c", "fn", "get_vts", None),
    ("src/nvim/ops.c", "fn", "get_vts_sum", None),
    ("src/nvim/register.c", "fn", "get_unname_register", None),
    ("src/nvim/register.c", "fn", "get_y_register", None),
    ("src/nvim/register.c", "fn", "get_y_previous", None),
    ("src/nvim/register.c", "fn", "op_reg_amount", None),
    ("src/nvim/register.c", "fn", "op_reg_get", None),
    ("src/nvim/register.c", "fn", "op_reg_set_previous", None),
    ("src/nvim/register.c", "fn", "op_reg_iter", None),
    ("src/nvim/register.c", "fn", "op_global_reg_iter", None),
    ("src/nvim/ops.c", "fn", "op_self_select", None),
    ("src/nvim/mbyte.c", "fn", "utf_char2bytes", None),
    ("src/nvim/strings.c", "fn", "vim_strchr", None),
    ("src/nvim/register.c", "fn", "valid_yank_reg", None),
]
PIN = os.path.join(HERE, "pins.txt")

PRELUDE = r"""// Prelude: what the pieces need from Neovim's headers, written as Neovim defines them
// (macros_defs.h, ascii_defs.h, func_attr.h, os/time_defs.h; checked by CHECKS below).
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <limits.h>
#include <string.h>
enum { MB_MAXBYTES = 30, };
#define FUNC_ATTR_NONNULL_ALL
#define NUL '\000'
#define Ctrl_A          1
#define Ctrl_X          24
#define ARRAY_SIZE(arr) \
  ((sizeof(arr)/sizeof((arr)[0])) \
   / ((size_t)(!(sizeof(arr) % sizeof((arr)[0])))))
#define ASCII_ISLOWER(c) ((unsigned)(c) >= 'a' && (unsigned)(c) <= 'z')
#define ASCII_ISUPPER(c) ((unsigned)(c) >= 'A' && (unsigned)(c) <= 'Z')
#define ASCII_ISALPHA(c) (ASCII_ISUPPER(c) || ASCII_ISLOWER(c))
#define ASCII_ISALNUM(c) (ASCII_ISALPHA(c) || ascii_isdigit(c))
#define CHAR_ORD_LOW(x)   ((uint8_t)(x) - 'a')
#define CHAR_ORD_UP(x)    ((uint8_t)(x) - 'A')
#define FUNC_ATTR_CONST
#define FUNC_ATTR_PURE
#define FUNC_ATTR_ALWAYS_INLINE
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_NONNULL_ARG(...)
typedef uint64_t Timestamp;
typedef int colnr_T;
typedef struct AdditionalData AdditionalData;
typedef struct oparg_opaque oparg_T;   // only a pointer to it is used here (normal_defs.h has the full struct)
#define MAX_SCHAR_SIZE 32
/*@ requires \false; assigns \nothing; */  // never reached: get_op_type must prove it
void internal_error(const char *where);
"""
CHECKS = [("src/nvim/ascii_defs.h", "#define NUL             '\\000'"),
          ("src/nvim/ascii_defs.h", "#define Ctrl_A          1"),
          ("src/nvim/ascii_defs.h", "#define Ctrl_X          24"),
          ("src/nvim/macros_defs.h", "#define ASCII_ISLOWER(c) ((unsigned)(c) >= 'a' && (unsigned)(c) <= 'z')"),
          ("src/nvim/macros_defs.h", "#define ASCII_ISUPPER(c) ((unsigned)(c) >= 'A' && (unsigned)(c) <= 'Z')"),
          ("src/nvim/macros_defs.h", "#define ASCII_ISALPHA(c) (ASCII_ISUPPER(c) || ASCII_ISLOWER(c))"),
          ("src/nvim/macros_defs.h", "#define ASCII_ISALNUM(c) (ASCII_ISALPHA(c) || ascii_isdigit(c))"),
          ("src/nvim/ascii_defs.h", "#define CHAR_ORD_LOW(x)   ((uint8_t)(x) - 'a')"),
          ("src/nvim/ascii_defs.h", "#define CHAR_ORD_UP(x)    ((uint8_t)(x) - 'A')"),
          ("src/nvim/macros_defs.h", "#define ARRAY_SIZE(arr) \\"),
          ("src/nvim/macros_defs.h", "  ((sizeof(arr)/sizeof((arr)[0])) \\"),
          ("src/nvim/macros_defs.h", "   / ((size_t)(!(sizeof(arr) % sizeof((arr)[0])))))"),
          ("src/nvim/os/time_defs.h", "typedef uint64_t Timestamp;"),
          ("src/nvim/pos_defs.h", "typedef int colnr_T;"),
          ("src/nvim/mbyte_defs.h", "  MB_MAXBYTES = 30,"),
          ("src/nvim/types_defs.h", "#define MAX_SCHAR_SIZE 32")]


def piece(tree, path, kind, name):
    lines = open(f"{tree}/{path}").read().split("\n")
    if kind == "fn":
        s, e = find(lines, name)
    else:
        a, b = name
        e = next(i for i in range(lines.index(a), len(lines)) if lines[i] == b)
        s = max(i for i in range(e + 1) if lines[i] == a)   # nearest start before the end line
    return s, "\n".join(lines[s:e + 1])


def main():
    tree, out = sys.argv[1], sys.argv[2]
    pin = "--pin" in sys.argv
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    fixed = "--fixed" in sys.argv
    want, fixed_keys = {}, set()
    if not pin:
        for l in open(PIN):
            k, h = l.split()
            want[k] = h
        if fixed:
            for l in open(os.path.join(HERE, "pins_fixed.txt")):
                k, h = l.split()
                want[k] = h; fixed_keys.add(k)
    parts, plain, pins = [PRELUDE], [PRELUDE], []
    for path, kind, name, _ in PIECES:
        s, text = piece(tree, path, kind, name)
        key = f"{path}:{name if kind == 'fn' else name[0][:40].replace(' ', '_')}"
        h = hashlib.sha256(text.encode()).hexdigest()
        pins.append(f"{key.replace(' ', '_')} {h}")
        if not pin and want.get(key.replace(' ', '_')) != h:
            sys.exit(f"build: {key} changed upstream: sha256 {h}")
        if kind == "fn" and LOGIC not in parts:   # reference logic after the types and globals
            parts.append(LOGIC); plain.append(LOGIC)
        c = CONTRACTS.get(name if kind == "fn" else None, "")
        if fixed and kind == "fn" and name in FIXED:
            c = FIXED[name]
        atext = text
        for anchor, ann in (LOOPS.get(name, []) if kind == "fn" else []):
            if atext.count(anchor + "\n") != 1:
                sys.exit(f"build: {name}: loop anchor not found once: {anchor}")
            ind = anchor[:len(anchor) - len(anchor.lstrip())]
            atext = atext.replace(anchor + "\n", f"{ind}{ann}\n{anchor}\n")
        parts.append(f"// {path}:{s + 1} (verbatim)\n" + (c + "\n" if c else "") + f"{atext}\n")
        plain.append(f"// {path}:{s + 1} (verbatim)\n{text}\n")
    if pin:
        open(PIN, "w").write("\n".join(pins) + "\n"); print("\n".join(pins)); return
    src = "\n".join(parts)
    ann = re.compile(r"^[ \t]*/\*@.*?\*/[^\n]*\n", re.M | re.S)
    if ann.sub("", "\n".join(plain)) != ann.sub("", src):
        sys.exit("build: annotations changed code")
    open(out, "w").write(src)


main()
