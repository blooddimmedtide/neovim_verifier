#!/bin/bash
# Usage: bash run_review.sh <dir holding strbuf.c and strbuf.h>
# Runs the reviewer's strengthened harnesses (harness_review.c), both char
# signednesses, same CBMC flags as ../cbmc/run_cbmc.sh. ONLY=<regex> filters.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); SRC=$(cd "$1" && pwd); status=0
for sign in signed --unsigned-char; do
for hu in r_init:66 r_new:66 r_free:4 r_free_to_string:4 r_calculate_new_size:66 r_resize:66 r_die:4 \
          r_debug_stats:4 r_append_string:8 r_helpers:8; do
  h=${hu%%:*}; u=${hu#*:}
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(cbmc "$HERE/harness_review.c" --function "$h" -I "$HERE" -I "$SRC" -DSTRBUF_C="\"$SRC/strbuf.c\"" \
        --arch x86_64 ${sign#signed} --bounds-check --pointer-check --signed-overflow-check --conversion-check \
        --unwind "$u" --unwindset calculate_new_size.0:66 --unwinding-assertions --sat-solver cadical 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|rror' | head -5; status=1; fi
done
done
exit $status
