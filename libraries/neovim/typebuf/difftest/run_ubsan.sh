#!/bin/bash
# Usage: bash run_ubsan.sh <neovim checkout> upstream|fixed
set -eu
HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d)
python3 -I "$HERE/../wp/build.py" "$1" "$W/tb.c" "$2" || [ $? -eq 2 ]
cp "$HERE/ubsan_cnt.c" "$W/"; sed -i 's/^#include "vp_typebuf.h"$//' "$W/tb.c"
gcc -O1 -std=gnu11 -fsanitize=undefined -fno-sanitize-recover=undefined -w -I "$HERE/../wp/stubs" -o "$W/t" "$W/ubsan_cnt.c"
"$W/t"
