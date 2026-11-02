#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> [mpack_core.c to use instead]
# Full-correctness proof of src/mpack/mpack_core.c with CBMC. The upstream file
# is included unchanged. Detects the fixed fork (no empty chunk at 4 GiB).
# ONLY=<regex> limits the run to matching harness names.
# Exit 0 = every harness proved, with all bounds proved enough.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
SRC=${2:-$NV/src/mpack/mpack_core.c}
D=""; grep -q 'MIN(\*buflen, (size_t)tokbuf->passthrough)' "$SRC" && D=-DMPACK_FIXED_CHUNK
if grep -n '__CPROVER' "$SRC"; then echo "CBMC builtin in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for h in h_tokbuf_init h_rtoken h_wtoken h_read h_write; do
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(cbmc "$HERE/harness.c" --function "$h" $D -I "$HERE" -I "$NV/src/mpack" -DMPACK_CORE_C="\"$SRC\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --signed-overflow-check --undefined-shift-check --unwind 20 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign${D:+, fixed}): proved"
  else echo "$h ($sign${D:+, fixed}): FAILED"; echo "$out" | grep -E 'FAILURE' | head -5; status=1; fi
done
done
exit $status
