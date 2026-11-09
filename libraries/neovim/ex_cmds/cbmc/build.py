#!/usr/bin/env python3
"""Verbatim extraction of sub_parse_flags from src/nvim/ex_cmds.c, sha256 pinned.
Usage: build.py <neovim checkout> <out.c>"""
import hashlib, sys
src = open(sys.argv[1] + "/src/nvim/ex_cmds.c").read().split("\n")
start = next(i for i, l in enumerate(src) if l.startswith("static char *sub_parse_flags("))
end = next(i for i in range(start, len(src)) if src[i] == "}")
body = "\n".join(src[start:end + 1]) + "\n"
PIN = "747f2efd6f896fa6d405692c6c1c51873df527342d3e8beceba9d583bbd5fd11"
h = hashlib.sha256(body.encode()).hexdigest()
if h != PIN:
    sys.exit(f"sub_parse_flags changed: sha256 {h}, pinned {PIN}")
open(sys.argv[2], "w").write(body.replace("  FUNC_ATTR_NONNULL_ALL FUNC_ATTR_NONNULL_RET\n", ""))
