#!/bin/bash
# Planted bugs in read_string: each must leave a WP goal unproved. Usage: bash run_mutants.sh <neovim checkout>
set -u
HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d); cp "$HERE/model.h" "$W/"
python3 -I "$HERE/annotate.py" "$1" "$W/orig.c" || exit 1
caught=0; total=0
while IFS='|' read -r name from to; do
  [ -z "$name" ] && continue; total=$((total+1))
  python3 -I -c 'import sys; s=open(sys.argv[1]).read(); assert s.count(sys.argv[2])==1; open(sys.argv[3],"w").write(s.replace(sys.argv[2],sys.argv[4]))' "$W/orig.c" "$from" "$W/rs.c" "$to" || { echo "$name: bad mutant"; continue; }
  (cd "$W" && frama-c -machdep x86_64 rs.c -wp -wp-fct read_string -wp-rte -wp-model Typed+Cast -wp-prover ${PROVERS:-z3,cvc5} -wp-timeout 20 -wp-cache none > m.log 2>&1)
  if grep -qE "Proved goals: +([0-9]+) / \1$" "$W/m.log"; then echo "$name: SURVIVED"; else echo "$name: caught"; caught=$((caught+1)); fi
done < "$HERE/mutants.txt"
echo "$caught/$total caught"; rm -rf "$W"; [ $caught -eq $total ]
