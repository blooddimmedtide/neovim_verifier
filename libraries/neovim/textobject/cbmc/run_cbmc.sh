#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>   Exit 0 = proved (both char signednesses).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/extract.py" "$NV" "$W/inmacro.c" >/dev/null || exit 1
status=0
for sign in signed --unsigned-char; do
  out=$(cbmc "$HERE/harness.c" --function h_inmacro -I "$HERE" -DINMACRO_C="\"$W/inmacro.c\"" ${CBMC_EXTRA:-} \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --signed-overflow-check --unwind 14 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "h_inmacro ($sign): proved"
  else echo "h_inmacro ($sign): FAILED"; echo "$out" | grep -E 'FAILURE' | head -5; status=1; fi
done
rm -rf "$W"; exit $status
