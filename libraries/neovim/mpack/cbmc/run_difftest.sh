#!/bin/bash
# Usage: bash run_difftest.sh <neovim checkout>   (a few seconds)
set -eu
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
gcc -O2 -fsigned-char -I "$HERE" -I "$NV/src/mpack" -DMPACK_CORE_C="\"$NV/src/mpack/mpack_core.c\"" "$HERE/difftest.c" -o "$W/dt"
"$W/dt"; rm -rf "$W"
