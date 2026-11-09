#!/bin/bash
# Usage: bash run_save.sh <neovim checkout>   CBMC proof of u_update_save_nr
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/build_save.py" "$NV" "$W/save.c" || exit 1
out=$(cbmc "$HERE/harness_save.c" --function h_update_save_nr -I "$HERE" -DSAVE_C="\"$W/save.c\"" \
      --arch x86_64 --bounds-check --pointer-check --signed-overflow-check 2>&1)
rm -rf "$W"
if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "h_update_save_nr: proved"
else echo "h_update_save_nr: FAILED"; echo "$out" | grep -E ": FAILURE$|error:" | head -5; exit 1; fi
