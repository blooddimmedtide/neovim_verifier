#!/bin/bash
# Usage: bash run_small.sh <neovim checkout>   CBMC proof of get_undolevel, zero_fmark_additional_data
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/build_small.py" "$NV" "$W/small.c" || exit 1
status=0
for h in h_get_undolevel h_zero_fmark; do
  out=$(cbmc "$HERE/harness_small.c" --function $h -I "$HERE" -DSMALL_C="\"$W/small.c\"" --arch x86_64 \
        --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check --memory-leak-check \
        --unwind 30 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h: proved"
  else echo "$h: FAILED"; echo "$out" | grep -E ": FAILURE$|error:" | head -5; status=1; fi
done
rm -rf "$W"; exit $status
