#!/usr/bin/env python3
"""Extract check_for_bom verbatim from src/nvim/fileio.c (sha256-pinned body)."""
import hashlib, re, sys
src = open(sys.argv[1] + "/src/nvim/fileio.c").read()
m = re.search(r"static char \*check_for_bom\(.*?\n}\n", src, re.S)
body = m.group(0)
h = hashlib.sha256(body.encode()).hexdigest()
PIN = "7f8580596c0adb77f132e183ba87243c6f18787155115dd743a9dc64394264b7"
if PIN != "PIN_PLACEHOLDER" and h != PIN:
    sys.exit(f"check_for_bom changed: {h}")
open(sys.argv[2], "w").write(body.replace("static char *", "char *", 1))
print(h)
