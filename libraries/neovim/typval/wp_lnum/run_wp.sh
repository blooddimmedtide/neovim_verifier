#!/bin/bash
# Usage: bash run_wp.sh <upstream tree> <fixed tree> [timeout]
# Expect: upstream tv_get_lnum_buf FAILS (the wrapping cast), fixed proves fully.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); T=${3:-30}; status=0
for mode in upstream fixed; do
  tree=$1; [ $mode = fixed ] && tree=$2
  W=$(mktemp -d); python3 -I "$HERE/build.py" "$tree" "$W/l.c" $mode || exit 1
  fs="tv_get_lnum_buf"; [ $mode = fixed ] && fs="tv_number_to_lnum tv_get_lnum_buf"
  for f in $fs; do
    (cd "$W" && frama-c -machdep x86_64 l.c -wp -wp-fct $f -wp-rte -warn-signed-downcast -warn-signed-overflow \
      -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout $T -wp-par "$(nproc)" -wp-cache none > wp_$f.log 2>&1)
    r=$(grep "Proved goals" "$W/wp_$f.log" | sed 's/.*goals: *//'); echo "$mode $f: ${r:-no result}"
    grep -E '\[(Timeout|Unknown|Failed)\]|User Error' "$W/wp_$f.log" | head -5 | sed 's/^/   /'
    ok=0; grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$f.log" && ok=1
    if [ $mode = fixed ] && [ $ok = 0 ]; then status=1; fi
    if [ $mode = upstream ] && [ $ok = 1 ]; then echo "   upstream unexpectedly proved"; status=1; fi
  done
done
exit $status
