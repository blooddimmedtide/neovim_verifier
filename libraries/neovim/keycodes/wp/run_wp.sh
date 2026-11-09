#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout at the pinned commit> [timeout_seconds] [function...]
# Proves each extracted keycodes.c function with Frama-C WP (+RTE), no admits.
# Exit 0 = every goal proved for every function, signed and unsigned char.
set -u -o pipefail
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-30}; shift 2 2>/dev/null || shift $#
FUNCS=${*:-name_to_mod_mask handle_x_keys simplify_key unsimplify_key get_mouse_button extract_modifiers}
W=$(mktemp -d); status=0
python3 -I "$HERE/build.py" "$NV" "$W/kc.c" || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/kc.c"; then echo "forbidden clause"; exit 1; fi
for chr in signed unsigned; do
  md="-machdep x86_64"; [ $chr = unsigned ] && md="-machdep $HERE/machdep_x86_64_uchar.yaml"
  for f in $FUNCS; do
    (cd "$W" && frama-c $md kc.c -wp -wp-fct "$f" -wp-rte -warn-signed-downcast \
       -wp-init-const -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" \
       -wp-cache none > "wp_${chr}_$f.log" 2>&1)
    r=$(grep -E "Proved goals" "$W/wp_${chr}_$f.log" | sed 's/.*goals: *//')
    echo "$chr $f: ${r:-no result}"
    grep -E '\[(Timeout|Unknown|Failed)\]|[Ee]rror' "$W/wp_${chr}_$f.log" | grep -v Wno | head -8 | sed 's/^/   /'
    grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_${chr}_$f.log" || status=1
  done
done
echo "logs: $W"; exit $status
