#!/bin/bash
# Usage: bash run_wp.sh <path/to/fzf.c> [timeout_seconds]
# Unbounded full-correctness proof of fzf.c's small helpers with Frama-C WP, no
# admits, no axioms. build.py makes an annotated copy of the exact text (sha256
# pinned to the fixed copy; stripping the /*@ */ comments gives the text back);
# each function is proved in its own run. Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
F=$(cd "$(dirname "$1")" && pwd)/$(basename "$1"); T=${2:-30}
W=$(mktemp -d); cp -r "$HERE/stubs" "$W/"; status=0
python3 -I "$HERE/build.py" "$F" "$W/fzfh.c" || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/fzfh.c" "$W"/stubs/*.h; then echo "forbidden clause"; exit 1; fi
run() {  # $1 = label, rest = frama-c selection options
  local l=$1; shift
  (cd "$W" && frama-c -machdep x86_64 -cpp-extra-args="-I stubs -I $(dirname "$F")" fzfh.c -wp "$@" -wp-rte \
     -warn-signed-downcast -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par 2 -wp-cache none > "wp_$l.log" 2>&1)
  local r; r=$(grep -E "Proved goals" "$W/wp_$l.log" | sed 's/.*goals: *//')
  echo "$l: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|error|Error' "$W/wp_$l.log" | head -5 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$l.log" || status=1
}
for f in ${ONLY:-index_byte leading_whitespaces trailing_whitespaces copy_runes copy_into_i16 \
         trim_whitespace_left max16 min64u char_class_of_ascii char_class_of bonus_for bonus_at \
         normalize_rune is_ascii}; do
  run "$f" -wp-fct "$f"
done
echo "logs: $W"; exit $status
