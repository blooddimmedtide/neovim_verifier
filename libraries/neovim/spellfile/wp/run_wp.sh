#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> [timeout_seconds]
# Proves read_string (fileio.c) for every count and file length with Frama-C WP, no admits.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-60}; W=$(mktemp -d)
cp "$HERE/model.h" "$W/"
python3 -I "$HERE/annotate.py" "$NV" "$W/rs.c" || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/rs.c" "$W/model.h"; then echo "forbidden clause"; exit 1; fi
(cd "$W" && frama-c -machdep x86_64 rs.c -wp -wp-fct read_string -wp-rte -wp-model Typed+Cast \
   -wp-prover ${PROVERS:-z3,cvc5} -wp-timeout "$T" -wp-smoke-tests -wp-cache none > wp.log 2>&1)
grep -iE "Proved goals|Smoke Tests|Timeout\]|Unknown\]|Failed\]|Error" "$W/wp.log"
grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp.log" || { echo "logs: $W"; exit 1; }
echo "read_string: proved"; rm -rf "$W"
