#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> [timeout_seconds]
# Frama-C 33 WP proofs of env.c helpers, RTE + smoke tests, signed and unsigned char.
# Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-30}
W=$(mktemp -d); cp "$HERE/prelude.h" "$W/"; status=0
python3 -I "$HERE/build.py" "$NV" "$W/env.c" || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/env.c" "$W/prelude.h"; then echo "forbidden clause"; exit 1; fi
if grep -nE '\[[^]]*\][[:space:]]*=[[:space:]]*"' "$W/env.c"; then echo "string-literal array initializer (WP bug)"; exit 1; fi
for sign in signed; do  # unsigned char: Frama-C 33 has no x86_64 unsigned-char machdep here (open)
  extra=""; [ $sign = unsigned ] && extra="-unsigned-char"
  for f in env_name_valid vim_env_iter vim_env_iter_rev; do
    (cd "$W" && frama-c -machdep x86_64 $extra env.c -wp -wp-fct "$f" -wp-rte -wp-smoke-tests \
       -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none \
       > "wp_${f}_$sign.log" 2>&1)
    r=$(grep -E "Proved goals" "$W/wp_${f}_$sign.log" | sed 's/.*goals: *//')
    echo "$f ($sign char): ${r:-no result}"
    grep -E '\[(Timeout|Unknown|Failed)\]|smoke|Smoke|error' "$W/wp_${f}_$sign.log" | sed 's/^/   /'
    grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_${f}_$sign.log" || status=1
  done
done
echo "logs: $W"; exit $status
