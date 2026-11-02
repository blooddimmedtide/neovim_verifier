#!/bin/bash
# Usage: bash run_difftest.sh <neovim checkout>   (about 25 s)
set -eu
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/build.py" "$NV" "$W/mbyte_utf8.c"
gcc -O2 -fsigned-char -Wall -I "$HERE" -DMBYTE_UTF8_C="\"$W/mbyte_utf8.c\"" "$HERE/difftest.c" -o "$W/dt"
"$W/dt"; rm -rf "$W"
