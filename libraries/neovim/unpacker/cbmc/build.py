"""Write a standalone C file holding exact upstream text from src/nvim/msgpack_rpc/unpacker.c.

Usage: python3 -I build.py <neovim checkout> <out.c>
The token reader is not stubbed: src/mpack/mpack_core.c and src/mpack/conv.c are
included whole (their sha256 is pinned here too), so the proof covers the real
mpack_rtoken / mpack_unpack_uint / mpack_unpack_sint. Each unpacker.c function is
checked against the sha256 recorded below; any upstream change stops the build.
"""
import hashlib, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools"))
from extract_c import find

F = "src/nvim/msgpack_rpc/unpacker.c"
FILES = {  # whole files included as they are (upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd)
    "src/mpack/mpack_core.c": None, "src/mpack/mpack_core.h": None,
    "src/mpack/conv.c": None, "src/mpack/conv.h": None,
}
REVIEWED = {
    "unpack_string": None,
    "unpack_array": None,
    "unpack_integer": None,
    "unpack_uint_or_sint": None,
    "parse_nop": None,
}
PIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pins.txt")

PRELUDE = r'''// Prelude: the Neovim types these functions use, as defined in
// src/nvim/api/private/defs.h (Integer, String, STRING_INIT) and
// src/nvim/api/private/helpers.h (cbuf_as_string macro).
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <sys/types.h>
#include "mpack_core.c"
#include "conv.c"
typedef int64_t Integer;
typedef struct {
  char *data;
  size_t size;
} String;
#define STRING_INIT { .data = NULL, .size = 0 }
#define cbuf_as_string(d, s) ((String) { .data = d, .size = s })
typedef struct mpack_parser_s mpack_parser_t;
typedef struct mpack_node_s mpack_node_t;
'''
CHECKS = [("src/nvim/api/private/defs.h", "typedef int64_t Integer;"),
          ("src/nvim/api/private/defs.h", "#define STRING_INIT { .data = NULL, .size = 0 }"),
          ("src/nvim/api/private/defs.h", "  char *data;"),
          ("src/nvim/api/private/defs.h", "  size_t size;"),
          ("src/nvim/api/private/defs.h", "} String;"),
          ("src/nvim/api/private/helpers.h", "#define cbuf_as_string(d, s) ((String) { .data = d, .size = s })")]


def pins():
    d = {}
    if os.path.exists(PIN):
        for l in open(PIN):
            k, v = l.split()
            d[k] = v
    return d


def main(tree, out, pin=False):
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    want = pins(); got = {}
    for path in FILES:
        got[path] = hashlib.sha256(open(f"{tree}/{path}", "rb").read()).hexdigest()
    lines = open(f"{tree}/{F}").read().split("\n")
    parts = [PRELUDE]
    for name in REVIEWED:
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1])
        got[name] = hashlib.sha256(piece.encode()).hexdigest()
        parts.append(f"// {F}:{s + 1} (verbatim)\n{piece}\n")
    if pin:
        open(PIN, "w").write("".join(f"{k} {v}\n" for k, v in got.items()))
    else:
        for k, v in got.items():
            if want.get(k) != v:
                sys.exit(f"build: {k} differs from the reviewed text: sha256 {v}")
    open(out, "w").write("\n".join(parts))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], len(sys.argv) > 3 and sys.argv[3] == "--pin")
