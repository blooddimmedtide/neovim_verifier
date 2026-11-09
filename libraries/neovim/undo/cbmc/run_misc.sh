#!/bin/bash
# Usage: bash run_misc.sh <neovim checkout> [prebuilt misc.c]   CBMC proof of u_clearline, u_update_named_mark
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
if [ $# -ge 2 ]; then cp "$2" "$W/misc.c"; else python3 -I "$HERE/build_misc.py" "$NV" "$W/misc.c" || exit 1; fi
status=0
for h in h_clearline h_update_named_mark; do
  out=$(cbmc "$HERE/harness_misc.c" --function $h -I "$HERE" -DMISC_C="\"$W/misc.c\"" --arch x86_64 \
        --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check --memory-leak-check 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h: proved"
  else echo "$h: FAILED"; echo "$out" | grep -E ": FAILURE$|error:" | head -5; status=1; fi
done
rm -rf "$W"; exit $status
