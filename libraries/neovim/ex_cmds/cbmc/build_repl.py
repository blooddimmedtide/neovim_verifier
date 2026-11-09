#!/usr/bin/env python3
"""Verbatim extraction of sub_get_replacement .. sub_set_replacement (src/nvim/ex_cmds.c),
sha256 pinned. Usage: build_repl.py <neovim checkout> <out.c>"""
import hashlib, sys
src = open(sys.argv[1] + "/src/nvim/ex_cmds.c").read().split("\n")
s = next(i for i, l in enumerate(src) if l.startswith("void sub_get_replacement("))
e = next(i for i, l in enumerate(src) if l.startswith("void sub_set_replacement("))
e = next(i for i in range(e, len(src)) if src[i] == "}")
body = "\n".join(src[s:e + 1]) + "\n"
PIN = "894fccb868d583416ad9db54d43418251ce9e84d5775432b6d3904846da659d2"
if hashlib.sha256(body.encode()).hexdigest() != PIN:
    sys.exit("sub_get/set_replacement changed")
open(sys.argv[2], "w").write(body.replace("  FUNC_ATTR_NONNULL_ALL\n", ""))
