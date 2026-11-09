#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> [timeout_seconds] [function...]
# Full-correctness proof of the register.c / ops.c helpers with Frama-C WP, no admits.
# build.py makes the annotated copy of the pinned text; each function (and the lemma) is
# proved in its own run, for signed and unsigned char. Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-30}; shift 2 2>/dev/null || shift $#
FUNCS=${*:-ascii_isdigit op_reg_index get_register_name reg_empty get_op_type op_on_lines op_is_change op_redoable get_op_char get_extra_op_char get_y_register get_y_previous op_reg_amount op_reg_get op_reg_set_previous}
W=$(mktemp -d); status=0
python3 -I "$HERE/build.py" "$NV" "$W/ro.c" || exit 1
if grep -nE '\b(admit|axiom|check|assumes)\b' "$W/ro.c"; then echo "forbidden clause"; exit 1; fi
run() {  # $1 = label, $2 = char signedness option, rest = frama-c selection options
  local l=$1 cs=$2; shift 2
  (cd "$W" && frama-c $cs ro.c -wp "$@" -wp-rte -warn-signed-downcast -wp-init-const \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none > "wp_$l.log" 2>&1)
  local r; r=$(grep -E "Proved goals" "$W/wp_$l.log" | sed 's/.*goals: *//')
  echo "$l: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|error|Error' "$W/wp_$l.log" | head -10 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$l.log" || status=1
}
run lemmas "-machdep x86_64" -wp-prop=@lemma
# x86_64 as is (signed char), and the same machine with unsigned char (only char_is_unsigned differs).
for cs in "-machdep x86_64" "-machdep $HERE/machdep_x86_64_uchar.yaml"; do
  tag=$([ "$cs" = "-machdep x86_64" ] && echo signed || echo unsigned)
  for f in $FUNCS; do run "$tag.$f" "$cs" -wp-fct "$f" -wp-prop=-@lemma; done
done
echo "logs: $W"; exit $status
