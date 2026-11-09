#!/usr/bin/env python3
"""Copy foldFind and foldReverseOrder verbatim out of src/nvim/fold.c (pinned commit) into fold_find.c.
Fails if the lines no longer match the pinned sha256. Usage: extract.py <neovim> <out.c>"""
import hashlib, sys
PIN = {"foldFind": (1020, 1049, "26873638040c5ba3be8254bddb4c89b6e8d0961465b0cfea9ee59b769de30b98"),
       "foldReverseOrder": (2587, 2599, "8c5791503a56bf3ba4f128d738ffa454d94ff562701567739246b606b1229433")}
src = open(sys.argv[1] + "/src/nvim/fold.c", encoding="utf-8").read().splitlines(keepends=True)
out = ['#include "fold_types.h"\n']
for name, (a, b, h) in PIN.items():
    text = "".join(src[a - 1:b])
    got = hashlib.sha256(text.encode()).hexdigest()
    if got != h:
        sys.exit(f"{name}: lines {a}-{b} changed (sha256 {got})")
    out.append(text)
open(sys.argv[2], "w").write("".join(out))
