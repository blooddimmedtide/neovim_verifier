#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> [timeout_seconds]
# Full-correctness proof of 15 string/memory functions of src/nvim/memory.c with
# Frama-C WP, no admits. build.py makes an annotated copy of the exact upstream text
# (sha256 pinned; stripping the /*@ */ comments gives the upstream text back), then
# each function, each ghost lemma function and the lemmas are proved in their own run.
# Needs CVC5 behind tools/bin/cvc5-fsq (tools/install.sh sets it up).
# Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-60}
W=$(mktemp -d); cp -r "$HERE/stubs" "$W/"; status=0
python3 -I "$HERE/build.py" "$NV" "$W/mem.c" || exit 1
# Behaviors' "assumes" are checked (complete/disjoint) and allowed; nothing unchecked.
if grep -nE '\b(admit|axiom|check)\b' "$W/mem.c" "$W"/stubs/*.h; then echo "forbidden clause"; exit 1; fi
# Frama-C 33 WP is unsound on string-literal array initializers (it assumes all zeros);
# refuse to run if one appears in the proved code.
if grep -nE '\[[^]]*\][[:space:]]*=[[:space:]]*"' "$W/mem.c"; then echo "string-literal array initializer (WP bug)"; exit 1; fi
run() {  # $1 = label, rest = frama-c selection options
  local l=$1; shift
  (cd "$W" && frama-c -machdep x86_64 -cpp-extra-args="-I stubs" mem.c -wp "$@" -wp-rte \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none > "wp_$l.log" 2>&1)
  local r; r=$(grep -E "Proved goals" "$W/wp_$l.log" | sed 's/.*goals: *//')
  echo "$l: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]' "$W/wp_$l.log" | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$l.log" || status=1
}
run lemmas -wp-prop=@lemma
for f in count_le count_gap xmemcpyz xstrnlen xstrchrnul xmemscan strchrsub memchrsub strcnt memcnt \
         xstpcpy xstpncpy xstrlcpy xstrlcat xmemrchr strequal strnequal; do
  run "$f" -wp-fct "$f"
done
echo "logs: $W"; exit $status
