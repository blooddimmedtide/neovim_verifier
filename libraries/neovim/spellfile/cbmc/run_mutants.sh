#!/bin/bash
# Planted bugs: each must make run_cbmc.sh fail. Usage: bash run_mutants.sh <neovim checkout>
set -u
HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d)
python3 -I "$HERE/build.py" "$1" "$W/orig.c" "$HERE/reviewed.sha256" || exit 1
caught=0; total=0
while IFS='|' read -r name from to; do
  [ -z "$name" ] && continue; total=$((total+1))
  python3 -I -c 'import sys; s=open(sys.argv[1]).read(); assert s.count(sys.argv[2])==1, sys.argv[2]; open(sys.argv[3],"w").write(s.replace(sys.argv[2],sys.argv[4]))' "$W/orig.c" "$from" "$W/m.c" "$to" || { echo "$name: bad mutant"; continue; }
  if bash "$HERE/run_cbmc.sh" "$1" "$W/m.c" >/dev/null 2>&1; then echo "$name: SURVIVED"; else echo "$name: caught"; caught=$((caught+1)); fi
done < "$HERE/mutants.txt"
echo "$caught/$total caught"; rm -rf "$W"; [ $caught -eq $total ]
