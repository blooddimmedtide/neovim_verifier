#!/bin/bash
# Usage: bash run_difftest.sh <neovim checkout>. Both char signednesses, gcc -O2.
set -u; HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d); st=0
python3 -I "$HERE/build.py" "$1" "$W/m.c" || exit 1
for sg in -fsigned-char -funsigned-char; do
  gcc -O2 $sg -w -I "$HERE" -DMBYTE_UTF8_C="\"$W/m.c\"" "$HERE/difftest.c" -o "$W/d" || st=1; echo "$sg: $("$W/d")"; [ "${PIPESTATUS[0]}" = 0 ] && "$W/d" >/dev/null || st=1
done; rm -rf "$W"; exit $st
