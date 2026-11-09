#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout at the pinned commit> [timeout_seconds] [function...]
# Proves each extracted keycodes.c function with Frama-C WP (+RTE), no admits.
# Exit 0 = every goal proved for every function, signed and unsigned char.
set -u -o pipefail
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-30}; shift 2 2>/dev/null || shift $#
FUNCS=${*:-name_to_mod_mask handle_x_keys get_mouse_button extract_modifiers}  # simplify_key, unsimplify_key, vim_unescape_ks: contracts here, not yet proved by WP (CBMC proves the first two)
W=$(mktemp -d); status=0
python3 -I "$HERE/build.py" "$NV" "$W/kc.c" || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/kc.c"; then echo "forbidden clause"; exit 1; fi
for chr in signed unsigned; do
  md="-machdep x86_64"; [ $chr = unsigned ] && md="-machdep $HERE/machdep_x86_64_uchar.yaml"
  for f in $FUNCS; do
    (cd "$W" && frama-c $md kc.c -wp -wp-fct "$f" -wp-rte -warn-signed-downcast \
       -wp-init-const -wp-smoke-tests -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" \
       -wp-cache none > "wp_${chr}_$f.log" 2>&1)
    r=$(grep -E "Proved goals" "$W/wp_${chr}_$f.log" | sed 's/.*goals: *//')
    echo "$chr $f: ${r:-no result}"
    grep -E '\[(Timeout|Unknown|Failed)\]|[Ee]rror' "$W/wp_${chr}_$f.log" | grep -v Wno | head -8 | sed 's/^/   /'
    # Smoke tests are on: a failed one means WP found the statement unreachable. The only
    # ones allowed are the dead branches of TOUPPER_ASC inside extract_modifiers (key is
    # already known to be a letter / upper case there), listed in ../CLAIM.md.
    bad=$(grep -E '\[(Timeout|Unknown|Failed)\]' "$W/wp_${chr}_$f.log" | grep -vE "extract_modifiers_wp_smoke_dead_code_s(120|144|174|175) " | wc -l)
    [ "$bad" = 0 ] && [ -n "$r" ] || status=1
  done
done
echo "logs: $W"; exit $status
