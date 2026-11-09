#!/bin/bash
# Usage: bash run_allow.sh <neovim checkout> [prebuilt allow.c]   CBMC proof of undo_allowed, corruption_error
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
if [ $# -ge 2 ]; then cp "$2" "$W/allow.c"; else python3 -I "$HERE/build_allow.py" "$NV" "$W/allow.c" || exit 1; fi
status=0
for h in h_undo_allowed h_corruption_error; do
  out=$(cbmc "$HERE/harness_allow.c" --function $h -I "$HERE" -DALLOW_C="\"$W/allow.c\"" --arch x86_64 \
        --bounds-check --pointer-check --signed-overflow-check --unwind 60 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h: proved"
  else echo "$h: FAILED"; echo "$out" | grep -E ": FAILURE$|error:" | head -5; status=1; fi
done
rm -rf "$W"; exit $status
