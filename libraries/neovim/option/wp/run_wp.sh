#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> [timeout_seconds] [function...]
# Full-correctness proof of option.c's comma-list helpers with Frama-C WP, no admits.
# Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-30}; shift 2 2>/dev/null || shift $#
FUNCS=${*:-key_prefix find_key_item remove_comma_item append_item prepend_item stropt_concat_with_comma valid_name check_option_listflag}
W=${WP_WORK:-$(mktemp -d)}; mkdir -p "$W/stubs"; cp "$HERE"/stubs/*.h "$HERE/../../memory/wp/stubs/vp_string.h" "$W/stubs/"; status=0
python3 -I "$HERE/build.py" "$NV" "$W/opt.c" || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/opt.c" "$W"/stubs/*.h; then echo "forbidden clause"; exit 1; fi
run() {  # $1 = label, rest = frama-c selection options
  local l=$1; shift
  (cd "$W" && frama-c -machdep x86_64 -cpp-extra-args="-I stubs" opt.c -wp "$@" -wp-rte -warn-signed-downcast \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none > "wp_$l.log" 2>&1)
  local r; r=$(grep -E "Proved goals" "$W/wp_$l.log" | sed 's/.*goals: *//')
  echo "$l: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|error|Error' "$W/wp_$l.log" | head -20 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$l.log" || status=1
}
run lemmas -wp-prop=@lemma
for f in $FUNCS; do run "$f" -wp-fct "$f"; done
echo "logs: $W"; exit $status
