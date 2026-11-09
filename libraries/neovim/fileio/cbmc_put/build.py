#!/usr/bin/env python3
"""Extract put_bytes and put_time verbatim from src/nvim/fileio.c; print sha256 of each."""
import hashlib, re, sys
src = open(sys.argv[1] + "/src/nvim/fileio.c").read()
out = []
for name in ("bool put_bytes", "int put_time"):
    m = re.search(re.escape(name) + r"\(.*?\n}\n", src, re.S)
    out.append(m.group(0)); print(name, hashlib.sha256(m.group(0).encode()).hexdigest())
open(sys.argv[2], "w").write("\n".join(out))
