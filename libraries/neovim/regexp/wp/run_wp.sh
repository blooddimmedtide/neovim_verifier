#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> [timeout_seconds]
# Full-correctness proof of regexp.c's getdecchrs with Frama-C WP, no admits.
# The pinned upstream text is proved under its overflow precondition
# (findings/regexp-getdecchrs-overflow.md); the fixed fork's text for every input.
# Needs CVC5 behind tools/bin/cvc5-fsq (tools/install.sh sets it up).
# Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-60}
W=$(mktemp -d); status=0
python3 -I "$HERE/build.py" "$NV" "$W/re.c" || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/re.c"; then echo "forbidden clause"; exit 1; fi
run() {  # $1 = label, rest = frama-c selection options
  local l=$1; shift
  (cd "$W" && frama-c -machdep x86_64 re.c -wp "$@" -wp-rte \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none > "wp_$l.log" 2>&1)
  local r; r=$(grep -E "Proved goals" "$W/wp_$l.log" | sed 's/.*goals: *//')
  echo "$l: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|error' "$W/wp_$l.log" | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$l.log" || status=1
}
for f in dval_mono getdecchrs; do
  run "$f" -wp-fct "$f"
done
echo "logs: $W"; exit $status
