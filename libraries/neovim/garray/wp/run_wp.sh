#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> <upstream|fixed> [timeout_seconds] [function...]
# Full-correctness proof of garray.c with Frama-C WP, no admits. build.py makes an
# annotated copy of the exact pinned text (stripping /*@ */ gives it back), then each
# function and the lemmas are proved in their own run. Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); MODE=$2; T=${3:-60}; shift 3 2>/dev/null || shift $#
FUNCS=${*:-concat_facts dedup_facts ga_clear ga_clear_strings ga_init ga_set_growsize ga_grow ga_remove_duplicate_strings ga_concat_strings ga_concat ga_concat_len ga_append ga_append_via_ptr}
W=$(mktemp -d); mkdir -p "$W/stubs"; cp "$HERE"/stubs/*.h "$HERE/../../memory/wp/stubs/vp_string.h" "$W/stubs/"; status=0
python3 -I "$HERE/build.py" "$NV" "$W/ga.c" "$MODE"; b=$?; [ $b = 0 ] || [ $b = 2 ] || exit 1; [ $b = 0 ] || status=1
if grep -nE '\b(admit|axiom|check)\b' "$W/ga.c" "$W"/stubs/*.h; then echo "forbidden clause"; exit 1; fi
run() {  # $1 = label, rest = frama-c selection options
  local l=$1; shift
  (cd "$W" && frama-c -machdep x86_64 -cpp-extra-args="-I stubs" ga.c -wp "$@" -wp-rte -warn-signed-downcast \
     -wp-model Typed+Cast -wp-smoke-tests -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none > "wp_$l.log" 2>&1)
  local r; r=$(grep -E "Proved goals" "$W/wp_$l.log" | sed 's/.*goals: *//')
  echo "$MODE $l: ${r:-no result}"; grep -iE '\[(Timeout|Unknown|Failed)\]|error|smoke|dead|unreachable' "$W/wp_$l.log" | head -20 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$l.log" || status=1
  # smoke tests: WP tries to prove each contract's assumptions inconsistent; all must fail to
  local sm; sm=$(grep -E "Smoke Tests:" "$W/wp_$l.log" | sed 's/.*Tests: *//'); echo "   smoke tests passed: ${sm:-none}"
  [ -z "$sm" ] || echo "$sm" | grep -qE "^([0-9]+) / \1$" || status=1
}
run lemmas -wp-prop=@lemma
for f in $FUNCS; do run "$f" -wp-fct "$f"; done
echo "logs: $W"; exit $status
