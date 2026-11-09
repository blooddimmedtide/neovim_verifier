#!/bin/bash
# Extracts verbatim upstream text (sha256 pinned in ../wp/contracts.py and below) into $2.
set -eu
NV=$1; OUT=$2
python3 -I - "$NV" "$OUT" <<'PY'
import hashlib, sys, pathlib
nv = pathlib.Path(sys.argv[1])
want = {
 ("src/nvim/os/env.c", "const void *vim_env_iter(const char delim,"): "a77dc5f52ef24422649b18a24ab266c0eb9492788c7a6b93d78429b2ac2c51b7",
 ("src/nvim/os/env.c", "const void *vim_env_iter_rev(const char delim,"): "0ecdd5f178f3fec1df3813ff470b1e770021b0f465c0f9135fc9efdf06fd2613",
 ("src/nvim/memory.c", "void *xmemrchr(const void *src, uint8_t c, size_t len)"): None,
}
out = []
for (f, start), pin in want.items():
    s = (nv / f).read_text(); i = s.index(start); j = s.index("\n}\n", i) + 3
    body = s[i:j]; h = hashlib.sha256(body.encode()).hexdigest()
    if pin and h != pin: sys.exit(f"{start}: changed {h}")
    print(f"{start[:40]}: {h}")
    out.append(body)
pathlib.Path(sys.argv[2]).write_text("".join(out))
PY
