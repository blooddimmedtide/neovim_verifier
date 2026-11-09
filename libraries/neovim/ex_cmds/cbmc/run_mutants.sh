#!/bin/bash
# Usage: bash run_mutants.sh <neovim checkout>. Each planted bug must make its proof fail.
# mutants.txt: run_cbmc.sh (sub_parse_flags); mutants_delim.txt: run_delim.sh; mutants_repl.txt: run_repl.sh.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); caught=0; total=0
for pair in mutants.txt:run_cbmc.sh mutants_delim.txt:run_delim.sh mutants_repl.txt:run_repl.sh; do
  list=${pair%%:*}; runner=${pair#*:}
  while IFS='|' read -r name from to; do
    [ -z "$name" ] && continue; total=$((total+1)); M=$(mktemp -d); mkdir -p "$M/src/nvim"
    python3 -I "$HERE/mutate.py" "$NV/src/nvim/ex_cmds.c" "$M/src/nvim/ex_cmds.c" "$from" "$to" \
      || { echo "BAD MUTANT $name"; exit 1; }
    # Mutants change the pinned text, so the copies skip the pin check.
    for b in build.py build_delim.py build_repl.py; do
      sed 's/^if h != PIN:/if False:/; s/^if hashlib.*PIN:/if False:/' "$HERE/$b" > "$M/$b"; done
    cp "$HERE"/harness*.c "$HERE/spec.h" "$HERE"/run_*.sh "$M/"
    if bash "$M/$runner" "$M" >/dev/null 2>&1; then echo "MISSED $name"; else echo "caught $name"; caught=$((caught+1)); fi
    rm -rf "$M"
  done < "$HERE/$list"
done
echo "$caught/$total caught"; [ $caught -eq $total ]
