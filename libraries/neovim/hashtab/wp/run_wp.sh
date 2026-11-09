#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> <upstream|fixed> [timeout_seconds] [function...]
# Full-correctness proof of hashtab.c with Frama-C WP, no admits. build.py makes an
# annotated copy of the exact pinned text (stripping /*@ */ gives it back); then
# bvlemmas.py checks the 64-bit arithmetic facts with Z3, and each function, each ghost
# lemma function and the WP lemmas are proved in their own run. Exit 0 = all proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); MODE=$2; T=${3:-60}; shift 3 2>/dev/null || shift $#
GHOSTS="isused_c p5_add reach_slot ncmp_facts hl_same key_hash all_keys_hash item_str not_found no_nul counts_zero find_null count_bounds rest_unused no_removed_counts ptrs_distinct used_pos vp_clear_table vp_clear_items vp_copy_items"
FUNCS_ALL="hash_init hash_clear hash_clear_all hash_find hash_find_len hash_lookup hash_debug_results hash_add hash_add_item hash_remove hash_lock hash_unlock hash_may_resize hash_hash hash_hash_len _hash_key_removed"
FUNCS=${*:-$GHOSTS $FUNCS_ALL}
W=$(mktemp -d); mkdir -p "$W/stubs"; cp "$HERE"/stubs/*.h "$HERE/../../memory/wp/stubs/vp_string.h" "$W/stubs/"; status=0
python3 -I "$HERE/build.py" "$NV" "$W/ht.c" "$MODE"; b=$?; [ $b = 0 ] || [ $b = 2 ] || exit 1; [ $b = 0 ] || status=1
if grep -nE '\b(admit|axiom|check)\b' "$W/ht.c" "$W"/stubs/*.h; then echo "forbidden clause"; exit 1; fi
if [ -z "${SKIP_BV:-}" ]; then
  python3 -I "$HERE/bvlemmas.py" > "$W/bvlemmas.log" 2>&1 || status=1
  echo "bit-vector lemmas: $(tail -1 "$W/bvlemmas.log")"
fi
run() {  # $1 = label, rest = frama-c selection options
  local l=$1; shift
  (cd "$W" && frama-c -machdep x86_64 -cpp-extra-args="-I stubs" ht.c -wp "$@" -wp-rte -warn-signed-downcast \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none > "wp_$l.log" 2>&1)
  local r; r=$(grep -E "Proved goals" "$W/wp_$l.log" | sed 's/.*goals: *//')
  echo "$MODE $l: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|error|Error' "$W/wp_$l.log" | head -20 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$l.log" || status=1
}
# WP proves its own lemmas; the bv_* lemmas are the Z3-checked statements above
run lemmas -wp-prop=p5_range,p5_unfive,str_nz,keq_short,keq_long,keq_flip,keq_sym,slot_range,nonull_grow,reach_grow
for f in $FUNCS; do run "$f" -wp-fct "$f"; done
echo "logs: $W"; exit $status
