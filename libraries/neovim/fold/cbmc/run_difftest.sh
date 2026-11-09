#!/bin/bash
# Usage: bash run_difftest.sh <neovim checkout>
set -eu
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/extract.py" "$NV" "$W/fold_find.c"
for s in -fsigned-char -funsigned-char; do
  gcc -O2 $s -fsanitize=address,undefined -fno-sanitize-recover=all -I "$HERE" \
      -DFOLD_FIND_C="\"$W/fold_find.c\"" "$HERE/difftest.c" -o "$W/dt"
  echo "difftest ($s):"; "$W/dt"
done
rm -rf "$W"
