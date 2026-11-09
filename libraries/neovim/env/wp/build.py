# Usage: python3 -I build.py <neovim tree> <out.c>
# Copies the verbatim upstream text of the target functions from src/nvim/os/env.c,
# checks its sha256 against the pin, and puts the ACSL contract in front.
import hashlib, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from contracts import CONTRACTS, PINS
src = (pathlib.Path(sys.argv[1]) / "src/nvim/os/env.c").read_text()
out = ['#include "prelude.h"\n']
for name, (start, contract) in CONTRACTS.items():
    i = src.index(start)
    j = src.index("\n}\n", i) + 3
    body = src[i:j]
    h = hashlib.sha256(body.encode()).hexdigest()
    if h != PINS[name]:
        sys.exit(f"{name}: upstream text changed ({h})")
    out.append("/*@ " + contract + " */\n" + body + "\n")
pathlib.Path(sys.argv[2]).write_text("".join(out))
