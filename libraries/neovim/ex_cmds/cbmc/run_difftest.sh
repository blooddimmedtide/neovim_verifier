#!/bin/bash
# Usage: bash run_difftest.sh <neovim checkout>
set -eu
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/build.py" "$NV" "$W/sub.c"
gcc -O2 -fsigned-char -Wall -I "$HERE" -DSUB_C="\"$W/sub.c\"" "$HERE/difftest.c" -o "$W/dt"
"$W/dt"; rm -rf "$W"
