#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>
# Proofs of src/nvim/sha256.c with CBMC; the file is included unchanged.
# ONLY=<regex> limits the run to matching harness names. Exit 0 = all proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
# The stub headers copy two macros; check they still match upstream.
grep -qxF "#define NUL             '\\000'" "$NV/src/nvim/ascii_defs.h" || { echo "NUL changed upstream"; exit 1; }
grep -qxF '#define STRCPY(d, s)        strcpy((char *)(d), (char *)(s))  // NOLINT(runtime/printf)' "$NV/src/nvim/memory.h" || { echo "STRCPY changed upstream"; exit 1; }
status=0
for h in ${HARNESSES:-h_forms h_start h_prims h_round h_sched h_endian}; do
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(cbmc "$HERE/harness.c" --function "$h" -I "$HERE/stubs" -I "$NV/src" -DSHA256_C="\"$NV/src/nvim/sha256.c\"" \
        --arch x86_64 --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
        --undefined-shift-check --unwind 66 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h: proved"
  else echo "$h: FAILED"; echo "$out" | grep -E 'FAILURE|ERROR|error' | head -5; status=1; fi
done
exit $status
