"""Write a standalone C file holding exact upstream text from src/nvim/msgpack_rpc/unpacker.c.

Usage: python3 -I build.py <neovim checkout> <out.c> [upstream|fixed] [--pin]
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
    "src/mpack/conv.c": None, "src/mpack/conv.h": None, "src/klib/kvec.h": None,
}
REVIEWED = {
    "unpack_string": None,
    "unpack_array": None,
    "unpack_integer": None,
    "unpack_uint_or_sint": None,
    "parse_nop": None,
    "api_parse_exit": None,
    "push_additional_data": None,
}
HERE = os.path.dirname(os.path.abspath(__file__))
PIN = os.path.join(HERE, "pins.txt")

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
#include "klib/kvec.h"
typedef struct {
  uint32_t nitems;
  uint32_t nbytes;
  char data[];
} AdditionalData;
typedef kvec_t(char) AdditionalDataBuilder;
typedef struct mpack_parser_s mpack_parser_t;
bool unpack_uint_or_sint(mpack_token_t tok, Integer *res);
typedef struct mpack_node_s mpack_node_t;
'''
CHECKS = [("src/nvim/api/private/defs.h", "typedef int64_t Integer;"),
          ("src/nvim/types_defs.h", "  uint32_t nitems;"), ("src/nvim/types_defs.h", "  uint32_t nbytes;"),
          ("src/nvim/types_defs.h", "  char data[];"), ("src/nvim/types_defs.h", "} AdditionalData;"),
          ("src/nvim/msgpack_rpc/unpacker.h", "typedef kvec_t(char) AdditionalDataBuilder;"),
          ("src/nvim/api/private/defs.h", "#define STRING_INIT { .data = NULL, .size = 0 }"),
          ("src/nvim/api/private/defs.h", "  char *data;"),
          ("src/nvim/api/private/defs.h", "  size_t size;"),
          ("src/nvim/api/private/defs.h", "} String;"),
          ("src/nvim/api/private/helpers.h", "#define cbuf_as_string(d, s) ((String) { .data = d, .size = s })")]


def BLOCKS(fixed):
    nb = "size_t" if fixed else "uint32_t"
    return [("src/nvim/api/private/defs.h", "typedef struct {\n  char *data;\n  size_t size;\n} String;\n"),
            ("src/nvim/types_defs.h",
             f"typedef struct {{\n  uint32_t nitems;\n  {nb} nbytes;\n  char data[];\n}} AdditionalData;\n")]


def pins(path=None):
    d = {}
    path = path or PIN
    if os.path.exists(path):
        for l in open(path):
            k, v = l.split()
            d[k] = v
    return d


def main(tree, out, mode="upstream", pin=False):
    fixed = mode == "fixed"
    global PIN, PRELUDE
    if fixed:  # verified_neovim fix: AdditionalData.nbytes is size_t
        PIN = os.path.join(HERE, "pins_fixed.txt")
        PRELUDE = PRELUDE.replace("  uint32_t nbytes;", "  size_t nbytes;")
        CHECKS[CHECKS.index(("src/nvim/types_defs.h", "  uint32_t nbytes;"))] = ("src/nvim/types_defs.h", "  size_t nbytes;")
    for path, text in CHECKS:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    for path, block in BLOCKS(fixed):  # whole structs, so no field can slip in unseen
        if block not in open(f"{tree}/{path}").read():
            sys.exit(f"build: {path} no longer contains the block:\n{block}")
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
    a = sys.argv[1:]
    main(a[0], a[1], a[2] if len(a) > 2 and a[2] != "--pin" else "upstream", "--pin" in a)
