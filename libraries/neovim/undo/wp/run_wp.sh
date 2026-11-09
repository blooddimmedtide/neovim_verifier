#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout>
# Frama-C WP proof of uhp_table_find (binary search over the sorted header table), any size.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d)
python3 -I "$HERE/../cbmc/build.py" "$NV" "$W/undo_io.c" || exit 1
python3 -I "$HERE/annotate.py" "$W/undo_io.c" "$W/undo_wp.c" || exit 1
if grep -nE '\badmit\b|\baxiom\b|\bcheck\b' "$W/undo_wp.c"; then echo "forbidden annotation"; exit 1; fi
out=$(frama-c -cpp-extra-args="-I$HERE/../cbmc" "$W/undo_wp.c" -wp -wp-rte -wp-model Typed+Cast \
      -wp-fct uhp_table_find -wp-prover z3,cvc5 -wp-timeout 30 -wp-cache none -wp-smoke-tests 2>&1)
echo "$out" | grep -E "Proved goals|Failed|Timeout|Unknown|error" 
rm -rf "$W"
echo "$out" | grep -qE "Proved goals: +([0-9]+) / \1$" || exit 1
