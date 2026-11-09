"""Standalone copy of unpacker_init from src/nvim/msgpack_rpc/unpacker.c, with the real
src/mpack/object.c (mpack_parser_init) and mpack_core.c (mpack_tokbuf_init) included whole.

Usage: python3 -I build_init.py <neovim checkout> <out.c> [upstream|fixed] [--pin]
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
    ("src/nvim/api/private/defs.h", "typedef enum {\n  kMessageTypeUnknown = -1,\n  // Per msgpack-rpc spec.\n  kMessageTypeRequest = 0,\n  kMessageTypeResponse = 1,\n  kMessageTypeNotification = 2,\n  kMessageTypeRedrawEvent = 3,\n} MessageType;\n"),
    ("src/nvim/api/private/defs.h", "#define ERROR_SET(e) ((e)->type != kErrorTypeNone)\n"),
]
PIECES = ["unpacker_init", "unpacker_parse_header"]


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
typedef struct { char opaque[24]; } Object;
typedef struct { void *fn; bool fast; bool ret_alloc; } MsgpackRpcRequestHandler;
typedef struct { void *fn; } UIClientHandler;
typedef struct { char opaque[64]; } GridLineEvent;
'''


STUBS = r'''
// Callees of unpacker_parse_header outside this file, as harness models (harness_hdr.c
// defines them and checks how they are called).
MsgpackRpcRequestHandler msgpack_rpc_get_handler_for(const char *name, size_t name_len, Error *error);
void api_set_error(Error *err, ErrorType errType, const char *format, ...);
'''


def main(tree, out, mode="upstream"):
    pf = "pins_init_fixed.txt" if mode == "fixed" else "pins_init.txt"
    for path, block in BLOCKS:
        if block not in open(f"{tree}/{path}").read():
            sys.exit(f"build_init: {path} no longer contains:\n{block}")
    pins = dict(l.split() for l in open(os.path.join(HERE, pf)))
    got = {"src/mpack/mpack_core.c": hashlib.sha256(open(f"{tree}/src/mpack/mpack_core.c", "rb").read()).hexdigest(),
           "src/mpack/object.c": hashlib.sha256(open(f"{tree}/src/mpack/object.c", "rb").read()).hexdigest(),
           "src/mpack/object.h": hashlib.sha256(open(f"{tree}/src/mpack/object.h", "rb").read()).hexdigest()}
    st = unpacker_struct(tree)
    got["struct Unpacker"] = hashlib.sha256(st.encode()).hexdigest()
    lines = open(f"{tree}/{F}").read().split("\n")
    code = []
    for name in PIECES:
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        got[name] = hashlib.sha256(piece.encode()).hexdigest()
        code.append(f"// {F}:{s + 1} (verbatim)\n{piece}\n")
    if "--pin" in sys.argv:
        with open(os.path.join(HERE, pf), "a") as f:
            for k, v in got.items():
                if k not in pins:
                    f.write(f"{k.replace(' ', '_')} {v}\n")
    else:
        for k, v in got.items():
            if pins.get(k.replace(" ", "_")) != v:
                sys.exit(f"build_init: {k} differs from the reviewed text: sha256 {v}")
    parts = [PRELUDE] + [b for _, b in BLOCKS if "enum" in b] + [b for _, b in BLOCKS if "enum" not in b]
    parts += [STUBS, "typedef struct Unpacker Unpacker;", st] + code
    open(out, "w").write("\n".join(parts))


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--pin"]
    main(a[0], a[1], a[2] if len(a) > 2 else "upstream")
