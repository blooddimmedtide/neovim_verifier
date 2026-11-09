#!/usr/bin/env python3
"""Verbatim extraction of check_regexp_delim and of the argument expression at its two call
sites in src/nvim/ex_cmds.c (body sha256 pinned). Usage: build_delim.py <nv> <out.c>"""
import hashlib, re, sys
src = open(sys.argv[1] + "/src/nvim/ex_cmds.c").read().split("\n")
s = next(i for i, l in enumerate(src) if l.startswith("static int check_regexp_delim("))
e = next(i for i in range(s, len(src)) if src[i] == "}")
body = "\n".join(src[s:e + 1]) + "\n"
PIN = "db106951c43fa74f0a0e6f8f69f160a9042a69aef67ea0cccd4ea72638d4ab70"
if hashlib.sha256(body.encode()).hexdigest() != PIN:
    sys.exit("check_regexp_delim changed")
args = [m.group(1) for l in src for m in [re.search(r"check_regexp_delim\((.*)\) == FAIL", l)] if m]
if len(args) != 2:
    sys.exit(f"expected 2 call sites, found {len(args)}")
out = body.replace("  FUNC_ATTR_PURE FUNC_ATTR_WARN_UNUSED_RESULT\n", "")
for i, a in enumerate(args):   # each call site's argument, as a function of the byte *cmd
    out += f"static int call_site_{i}(char *cmd) {{ return {a}; }}\n"
open(sys.argv[2], "w").write(out)
