#!/bin/bash
# Usage: bash run.sh [timeout] [function...]  -- one WP run per function, exit 0 = all proved
V=$HOME/.vpipe/nix; export PATH=$V/frama-c/bin:$V/why3/bin:$V/z3/bin:$V/cvc5/bin:$PATH
HERE=$(cd "$(dirname "$0")" && pwd); T=${1:-30}; shift 2>/dev/null
FUNCS=${*:-mh_realloc mh_clear mh_find_bucket_int mh_get_int map_ref_int_ptr_t}
status=0
for f in $FUNCS; do
  (cd "$HERE" && frama-c -machdep x86_64 -cpp-extra-args="-I stubs" map_int.c -wp -wp-fct $f -wp-rte -warn-signed-downcast \
    -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none > "/tmp/wp_$f.log" 2>&1)
  r=$(grep -E "Proved goals" /tmp/wp_$f.log | sed 's/.*goals: *//'); echo "$f: ${r:-no result}"
  grep -E '\[(Timeout|Unknown|Failed)\]|rror' /tmp/wp_$f.log | head -12 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" /tmp/wp_$f.log || status=1
done
exit $status
