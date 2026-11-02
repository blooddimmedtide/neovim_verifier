#!/bin/bash
# Usage: bash run_difftest.sh <neovim checkout> <upstream|fixed> [iterations]
# Builds the proof's copy of garray.c (exact pinned text), compiles it with gcc -O2 for
# signed and unsigned char under ASan/UBSan, and compares it with plain references.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); MODE=$2; N=${3:-100000}
W=$(mktemp -d); cp "$HERE"/../wp/stubs/*.h "$HERE/../../memory/wp/stubs/vp_string.h" "$W/"
python3 -I "$HERE/../wp/build.py" "$NV" "$W/ga.c" "$MODE"
sed -i 's/#include "vp_garray.h"/#include <stddef.h>\n#include <stdint.h>\ntypedef enum { kPathCmpLiteral = 1 } PathCmpFlags;/' "$W/ga.c"
for sign in -fsigned-char -funsigned-char; do
  gcc -O2 $sign -w -fsanitize=address,undefined -fno-sanitize-recover=all -DGA_C="\"$W/ga.c\"" \
      "$HERE/difftest.c" -o "$W/dt"
  echo "$MODE $sign: $("$W/dt" "$N" 12345)"
done
rm -rf "$W"
