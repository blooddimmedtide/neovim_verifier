#!/bin/bash
# Usage: bash run_mutants.sh <neovim checkout>. Each mutant must make run_cbmc.sh fail.
HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d); caught=0; total=0
while IFS=$'\t' read -r from to; do
  [ -z "$from" ] && continue; total=$((total+1))
  mkdir -p "$W/nv/src/nvim"; python3 -I - "$1/src/nvim/menu.c" "$W/nv/src/nvim/menu.c" "$from" "$to" <<'PY'
import sys; s=open(sys.argv[1]).read(); assert s.count(sys.argv[3])>=1, sys.argv[3]
open(sys.argv[2],"w").write(s.replace(sys.argv[3], sys.argv[4], 1))
PY
  # pins would reject the mutant, so rebuild pins for it in a copy of this dir
  cp -r "$HERE" "$W/h"; python3 -I "$W/h/build.py" "$W/nv" /dev/null --print-pins > "$W/h/pins.txt"
  if bash "$W/h/run_cbmc.sh" "$W/nv" >/dev/null 2>&1; then echo "MISSED: $from -> $to"; else echo "caught: $from -> $to"; caught=$((caught+1)); fi
  rm -rf "$W/h"
done < "$HERE/mutants.txt"
echo "$caught/$total caught"; rm -rf "$W"; [ $caught -eq $total ]
