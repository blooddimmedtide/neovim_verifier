#!/bin/bash
# Usage: bash run_bytes.sh <neovim checkout>   (sha256_bytes with recorded start/update/finish)
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
goto-cc "$HERE/harness_bytes.c" -o "$W/a.goto" --function h_bytes -I "$HERE/stubs" -I "$NV/src" \
   -DSHA256_C="\"$NV/src/nvim/sha256.c\"" || exit 1
goto-instrument --replace-calls sha256_start:rec_start --replace-calls sha256_update:rec_update \
   --replace-calls sha256_finish:rec_finish --replace-calls sha256_self_test:rec_self_test \
   "$W/a.goto" "$W/b.goto" >/dev/null || exit 1
out=$(cbmc "$W/b.goto" --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
      --undefined-shift-check --unwind 70 --unwinding-assertions 2>&1)
if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "h_bytes: proved"; rm -rf "$W"
else echo "h_bytes: FAILED"; echo "$out" | grep -E 'FAILURE|ERROR|error' | head -8; exit 1; fi
