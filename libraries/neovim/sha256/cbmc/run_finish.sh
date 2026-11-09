#!/bin/bash
# Usage: bash run_finish.sh <neovim checkout>   (sha256_finish with a recording sha256_process)
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
goto-cc "$HERE/harness_finish.c" -o "$W/a.goto" --function h_finish -I "$HERE/stubs" -I "$NV/src" \
   -DSHA256_C="\"$NV/src/nvim/sha256.c\"" || exit 1
goto-instrument --replace-calls sha256_process:rec_process "$W/a.goto" "$W/b.goto" >/dev/null || exit 1
out=$(cbmc "$W/b.goto" --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
      --undefined-shift-check --unwind 70 --unwinding-assertions 2>&1)
if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "h_finish: proved"; rm -rf "$W"
else echo "h_finish: FAILED"; echo "$out" | grep -E 'FAILURE|ERROR|error' | head -8; exit 1; fi
