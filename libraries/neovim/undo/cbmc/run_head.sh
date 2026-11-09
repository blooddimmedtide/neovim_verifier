#!/bin/bash
# Usage: bash run_head.sh <neovim checkout>   CBMC proof of u_get_headentry, u_getbot
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
if [ $# -ge 2 ]; then cp "$2" "$W/head.c"; else python3 -I "$HERE/build_head.py" "$NV" "$W/head.c" || exit 1; fi
status=0
for h in h_get_headentry h_getbot; do
  out=$(cbmc "$HERE/harness_head.c" --function $h -I "$HERE" -DHEAD_C="\"$W/head.c\"" --arch x86_64 \
        --bounds-check --pointer-check --signed-overflow-check --unwind 5 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h: proved"
  else echo "$h: FAILED"; echo "$out" | grep -E ": FAILURE$|error:" | head -5; status=1; fi
done
rm -rf "$W"; exit $status
