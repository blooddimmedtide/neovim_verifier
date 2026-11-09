#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>. Exit 0 = all proved (lists of up to MAXN=4 entries).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d); status=0
python3 -I "$HERE/build.py" "$NV" "$W/i.c" || exit 1
for sign in "" --unsigned-char; do
  for h in h_count_first h_padding h_start h_at h_fromto; do
    out=$(timeout 900 cbmc "$HERE/harness.c" --function $h -DINDENT_C="\"$W/i.c\"" --arch x86_64 $sign \
          --bounds-check --pointer-check --signed-overflow-check --div-by-zero-check \
          --undefined-shift-check --unwind 8 --unwinding-assertions 2>&1)
    if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ${sign:-signed-char}: proved"
    else echo "$h ${sign:-signed-char}: FAILED"; echo "$out" | grep -E "FAILURE|error" | head -5; status=1; fi
  done
done
rm -rf "$W"; exit $status
