#!/bin/bash
# Usage: bash run_difftest.sh <neovim checkout> <upstream|fixed>
set -eu
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); MODE=$2; W=$(mktemp -d)
python3 -I "$HERE/../wp/build.py" "$NV" "$W/path_built.c" "$MODE"
D=""; [ "$MODE" = fixed ] && D=-DFIXED
for sign in -fsigned-char -funsigned-char; do
  gcc -O2 $sign $D -w -fsanitize=address,undefined -fno-sanitize-recover=all -I "$W" \
      -I "$HERE/../wp/stubs" -I "$HERE/../../memory/wp/stubs" "$HERE/difftest.c" -o "$W/dt"
  echo "$MODE $sign: $("$W/dt" | tail -1)"; "$W/dt" > /dev/null
done
