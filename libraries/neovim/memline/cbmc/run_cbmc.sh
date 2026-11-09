#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout at 7b87ce8>. Exit 0 = both signednesses pass.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d); st=0
python3 -I "$HERE/build.py" "$1" "$W/b0.c" || exit 1
for h in harness harness_b0; do
cat "$W/b0.c" "$HERE/$h.c" > "$W/all.c"
for sign in "" "--unsigned-char"; do
  cbmc "$W/all.c" --function main $sign --bounds-check --pointer-check --signed-overflow-check \
    --unsigned-overflow-check --undefined-shift-check --unwinding-assertions --unwind 901 > "$W/log" 2>&1
  r=$(grep -E "VERIFICATION (SUCCESSFUL|FAILED)" "$W/log"); echo "$h char ${sign:-signed}: $r"
  [ "$r" = "VERIFICATION SUCCESSFUL" ] || { st=1; grep FAILURE "$W/log" | head; }
done
done
exit $st
