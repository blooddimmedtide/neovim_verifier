#!/usr/bin/env python3
"""Extract need_conversion and get_fio_flags verbatim from src/nvim/fileio.c; print sha256."""
import hashlib, re, sys
src = open(sys.argv[1] + "/src/nvim/fileio.c").read()
out = []
for name in ("bool need_conversion", "int get_fio_flags"):
    m = re.search(re.escape(name) + r"\(.*?\n}\n", src, re.S)
    b = m.group(0).replace("  FUNC_ATTR_NONNULL_ALL FUNC_ATTR_WARN_UNUSED_RESULT\n", "")
    out.append(b); print(name, hashlib.sha256(m.group(0).encode()).hexdigest())
open(sys.argv[2], "w").write("int get_fio_flags(const char *name);\n" + "\n".join(out))
