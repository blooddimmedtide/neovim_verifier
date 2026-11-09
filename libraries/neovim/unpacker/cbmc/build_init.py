"""Standalone copy of unpacker_init from src/nvim/msgpack_rpc/unpacker.c, with the real
src/mpack/object.c (mpack_parser_init) and mpack_core.c (mpack_tokbuf_init) included whole.

Usage: python3 -I build_init.py <neovim checkout> <out.c>
The Unpacker struct body is copied verbatim from unpacker.h (checked as one block). Field
types unpacker_init never touches (Object, handlers, GridLineEvent) are opaque placeholders
of fixed size: the proof shows which fields are written; those fields' layout does not
matter to it. Pins: pins_init.txt.
"""
import hashlib, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find

F = "src/nvim/msgpack_rpc/unpacker.c"
BLOCKS = [
    ("src/nvim/memory_defs.h", "typedef struct {\n  char *cur_blk;\n  size_t pos, size;\n} Arena;\n"),
    ("src/nvim/memory_defs.h", "#define ARENA_EMPTY { .cur_blk = NULL, .pos = 0, .size = 0 }\n"),
    ("src/nvim/api/private/defs.h", "#define ERROR_INIT ((Error) { .type = kErrorTypeNone, .msg = NULL })\n"),
    ("src/nvim/api/private/defs.h", "typedef enum {\n  kErrorTypeNone = -1,\n  kErrorTypeException,\n  kErrorTypeValidation,\n} ErrorType;\n"),
    ("src/nvim/api/private/defs.h", "typedef struct {\n  ErrorType type;\n  char *msg;\n} Error;\n"),
]


def unpacker_struct(tree):
    h = open(f"{tree}/src/nvim/msgpack_rpc/unpacker.h").read()
    m = re.search(r"^struct Unpacker \{\n.*?^\};\n", h, re.S | re.M)
    if not m:
        sys.exit("build_init: struct Unpacker not found")
    return m.group(0)


PRELUDE = r'''#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include "mpack_core.c"
#include "object.c"
// Opaque placeholders for field types unpacker_init does not touch.
typedef enum { kMessageTypeUnknown = -1 } MessageType;
typedef struct { char opaque[24]; } Object;
typedef struct { void *fn; bool fast; bool ret_alloc; } MsgpackRpcRequestHandler;
typedef struct { void *fn; } UIClientHandler;
typedef struct { char opaque[64]; } GridLineEvent;
'''


def main(tree, out):
    for path, block in BLOCKS:
        if block not in open(f"{tree}/{path}").read():
            sys.exit(f"build_init: {path} no longer contains:\n{block}")
    pins = dict(l.split() for l in open(os.path.join(HERE, "pins_init.txt")))
    got = {"src/mpack/mpack_core.c": hashlib.sha256(open(f"{tree}/src/mpack/mpack_core.c", "rb").read()).hexdigest(),
           "src/mpack/object.c": hashlib.sha256(open(f"{tree}/src/mpack/object.c", "rb").read()).hexdigest(),
           "src/mpack/object.h": hashlib.sha256(open(f"{tree}/src/mpack/object.h", "rb").read()).hexdigest()}
    st = unpacker_struct(tree)
    got["struct Unpacker"] = hashlib.sha256(st.encode()).hexdigest()
    lines = open(f"{tree}/{F}").read().split("\n")
    s, e = find(lines, "unpacker_init")
    piece = "\n".join(lines[s:e + 1])
    got["unpacker_init"] = hashlib.sha256(piece.encode()).hexdigest()
    if "--pin" in sys.argv:
        with open(os.path.join(HERE, "pins_init.txt"), "a") as f:
            for k, v in got.items():
                if k not in pins:
                    f.write(f"{k.replace(' ', '_')} {v}\n")
    else:
        for k, v in got.items():
            if pins.get(k.replace(" ", "_")) != v:
                sys.exit(f"build_init: {k} differs from the reviewed text: sha256 {v}")
    parts = [PRELUDE] + [b for _, b in BLOCKS[::-1] if "enum" in b] + [b for _, b in BLOCKS if "enum" not in b]
    parts += ["typedef struct Unpacker Unpacker;", st, f"// {F}:{s + 1} (verbatim)\n{piece}\n"]
    open(out, "w").write("\n".join(parts))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
