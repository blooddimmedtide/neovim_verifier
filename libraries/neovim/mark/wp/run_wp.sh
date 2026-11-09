#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> [timeout_seconds] [function...]
# Full-correctness WP proof of mark.c functions, no admits. Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-60}; shift 2 2>/dev/null || shift $#
FUNCS=${*:-mark_view_make mark_check_line_bounds next_buffer_mark mark_jumplist_iter mark_global_iter}
W=$(mktemp -d); mkdir -p "$W/stubs"; cp "$HERE"/stubs/*.h "$W/stubs/"; status=0
python3 -I "$HERE/build.py" "$NV" "$W/mark.c" || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/mark.c" "$W"/stubs/*.h; then echo "forbidden clause"; exit 1; fi
for f in $FUNCS; do
  (cd "$W" && frama-c -machdep x86_64 -cpp-extra-args="-I stubs" mark.c -wp -wp-fct "$f" -wp-rte -warn-signed-downcast \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none > "wp_$f.log" 2>&1)
  r=$(grep -E "Proved goals" "$W/wp_$f.log" | sed 's/.*goals: *//')
  echo "$f: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|error|Error' "$W/wp_$f.log" | head -20 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$f.log" || status=1
done
echo "logs: $W"; exit $status
