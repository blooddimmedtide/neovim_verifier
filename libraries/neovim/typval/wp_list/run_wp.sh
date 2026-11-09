#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> [timeout_seconds] [function...]
# Full-correctness WP proof of the typval list functions, no admits. Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-30}; shift 2 2>/dev/null || shift $#
FUNCS=${*:-tv_list_len tv_list_uidx tv_list_find tv_list_idx_of_item tv_list_find_index tv_list_check_range_index_one tv_list_check_range_index_two tv_list_reverse}
W=$(mktemp -d); status=0
python3 -I "$HERE/build.py" "$NV" "$W/tvl.c" || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/tvl.c"; then echo "forbidden clause"; exit 1; fi
for CH in ""; do  # no function here reads a plain char
for f in $FUNCS; do
  (cd "$W" && frama-c -machdep x86_64 $CH tvl.c -wp -wp-fct "$f" -wp-rte -warn-signed-downcast -warn-signed-overflow \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none > "wp_$f$CH.log" 2>&1)
  r=$(grep -E "Proved goals" "$W/wp_$f$CH.log" | sed 's/.*goals: *//')
  echo "$f${CH:+ ($CH)}: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|\[kernel\].*(error|Error)|User Error' "$W/wp_$f$CH.log" | head -10 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$f$CH.log" || status=1
done; done
echo "logs: $W"; exit $status
