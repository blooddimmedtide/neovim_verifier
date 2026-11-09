#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> [upstream|fixed] [timeout_seconds] [functions...]
# Proves the typeahead/stuff buffer functions of src/nvim/input.c with Frama-C WP, one
# run per function. Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); MODE=${2:-upstream}; T=${3:-30}; shift 3 2>/dev/null
W=$(mktemp -d); cp -r "$HERE/stubs" "$W/"; status=0
python3 -I "$HERE/build.py" "$NV" "$W/tb.c" "$MODE"; rc=$?; [ $rc -eq 0 ] || status=1; [ $rc -le 2 ] || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/tb.c" "$W"/stubs/*.h; then echo "forbidden clause"; exit 1; fi
if grep -nE '\[[^]]*\][[:space:]]*=[[:space:]]*"' "$W/tb.c"; then echo "string-literal array initializer (WP bug)"; exit 1; fi
FNS=${*:-free_buff add_buff read_readbuf read_readbuffers start_stuff stuff_empty readbuf1_empty init_typebuf ins_typebuf typebuf_changed typebuf_typed typebuf_maplen del_typebuf alloc_typebuf free_typebuf put_string_in_typebuf}
run() {
  local f=$1
  (cd "$W" && timeout "${WP_WALL:-600}" frama-c -machdep x86_64 -cpp-extra-args="-I stubs" tb.c -wp -wp-fct "$f" -wp-rte \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none -wp-smoke-tests > "wp_$f.log" 2>&1)
  local r; r=$(grep -E "Proved goals" "$W/wp_$f.log" | sed 's/.*goals: *//')
  echo "$f: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|^\[kernel\].*[Ee]rror|User Error' "$W/wp_$f.log" | head -12 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$f.log" || status=1
  # smoke tests: a precondition, call or branch that WP finds dead means a contradictory spec
  if grep -nE "Doomed|Failed smoke" "$W/wp_$f.log" | grep -v "Proved goals" | head -5 | sed 's/^/   SMOKE: /' | grep .; then status=1; fi
}
for f in $FNS; do grep -q "^[a-z].*\b$f(" "$W/tb.c" && run "$f" || { echo "$f: not built"; status=1; }; done
echo "logs: $W"; exit $status
