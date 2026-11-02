#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> [strbuf.c to use instead]
# CBMC proofs of src/cjson/strbuf.c (upstream or the fixed fork; both are pinned below).
# ONLY=<regex> limits the run to matching harness names (used by run_mutants.py).
# Exit 0 = every harness proved, with all loop bounds proved enough.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d)
cp "$NV/src/cjson/strbuf.h" "$W/"; cp "${2:-$NV/src/cjson/strbuf.c}" "$W/strbuf.c"
UP_C=03ff8345479a1b9e09f3e0add9ae3a493aecd00847ae94bc0dc8f8650ecccd86     # 7b87ce8
FIX_C=f245f035a37b8ab78b989273cbacdd7fb0e620589d684c52438c11df97cb24fd    # fork: size_t index
H=80ab74522aacf9b8ad68b7906faed874685fcec7b3b6ac373baf5182ffde03c6
[ "$(sha256sum < "$W/strbuf.h" | cut -d' ' -f1)" = "$H" ] || { echo "strbuf.h changed upstream"; exit 1; }
c=$(sha256sum < "$W/strbuf.c" | cut -d' ' -f1)
if [ $# -lt 2 ] && [ "$c" != "$UP_C" ] && [ "$c" != "$FIX_C" ]; then echo "strbuf.c changed upstream: $c"; exit 1; fi
if grep -n '__CPROVER' "$W/strbuf.c" "$W/strbuf.h"; then echo "CPROVER in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for hu in h_init:66 h_new:66 h_free:4 h_free_to_string:4 h_calculate_new_size:66 h_resize:66 h_die:4 \
          h_debug_stats:4 h_append_string:8 h_helpers:8; do
  h=${hu%%:*}; u=${hu#*:}
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(cbmc "$HERE/harness.c" --function "$h" -I "$HERE" -I "$W" -DSTRBUF_C="\"$W/strbuf.c\"" \
        --arch x86_64 ${sign#signed} --bounds-check --pointer-check --signed-overflow-check --conversion-check \
        --unwind "$u" --unwindset calculate_new_size.0:66 --unwinding-assertions --sat-solver cadical 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|rror' | head -5; status=1; fi
done
done
rm -rf "$W"; exit $status
