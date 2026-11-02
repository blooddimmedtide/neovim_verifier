#!/bin/bash
# Usage: bash run_difftest.sh <neovim checkout> [iterations]
# Builds the annotated copy (exact upstream code), compiles it with gcc -O2 (signed and
# unsigned char) under ASan/UBSan, and compares it with naive references.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); N=${2:-2000000}
W=$(mktemp -d); cp -r "$HERE/../wp/stubs" "$W/"
python3 -I "$HERE/../wp/build.py" "$NV" "$W/cs.c"
# the proof copy declares xmalloc/xstrchrnul, string.h and strtoimax through stubs; use the real libc here
grep -v '#include "vp_string.h"\|#include "nvim/memory.h"\|#include "vp_strtoimax.h"' "$W/cs.c" > "$W/cs_real.c"
for sign in -fsigned-char -funsigned-char; do
  gcc -O2 $sign -fsanitize=address,undefined -fno-sanitize-recover=all -DCS_C="\"$W/cs_real.c\"" \
      "$HERE/difftest.c" -o "$W/dt"
  echo "$sign: $("$W/dt" "$N" 12345)"
done
rm -rf "$W"
