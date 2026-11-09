#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> <upstream|fixed> [timeout_seconds] [function...]
# Full-correctness WP proof of marktree.c leaf functions, no admits. Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); MODE=$2; T=${3:-30}; shift 3 2>/dev/null || shift $#
FUNCS=${*:-mt_end mt_invalid pos_leq pos_less relative unrelative compose key_cmp intersection_has intersect_item_pos marktree_getp_aux marktree_itr_node_done marktree_itr_pos itr_eq}  # meta_* are proved with CBMC (../cbmc)
W=$(mktemp -d); mkdir -p "$W/stubs"; cp "$HERE"/stubs/*.h "$W/stubs/"; status=0
python3 -I "$HERE/build.py" "$NV" "$W/mt.c" "$MODE" || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/mt.c" "$W"/stubs/vp_marktree.h; then echo "forbidden clause"; exit 1; fi
run() {
  local l=$1; shift
  (cd "$W" && frama-c -machdep x86_64 -cpp-extra-args="-I stubs" mt.c -wp "$@" -wp-rte -warn-signed-downcast \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none > "wp_$l.log" 2>&1)
  local r; r=$(grep -E "Proved goals" "$W/wp_$l.log" | sed 's/.*goals: *//')
  echo "$MODE $l: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|error|Error' "$W/wp_$l.log" | head -20 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$l.log" || status=1
}
run lemmas -wp-prop=@lemma
for f in $FUNCS; do run "$f" -wp-fct "$f"; done
echo "logs: $W"; exit $status
