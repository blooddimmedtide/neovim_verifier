#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>. Exit 0 = all proved (both char signednesses).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d); status=0
python3 -I "$HERE/build.py" "$NV" "$W/w.c" || exit 1
for sgn in "" --unsigned-char; do
  for h in h_default_scroll h_set_fraction h_check_height h_check_width h_global_stl; do
    out=$(cbmc "$HERE/harness.c" --function $h -DWINDOW_C="\"$W/w.c\"" --arch x86_64 $sgn --bounds-check \
          --pointer-check --signed-overflow-check --undefined-shift-check --unwind 6 --no-malloc-may-fail --sat-solver cadical --unwinding-assertions 2>&1)
    if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ${sgn:-signed-char}: proved"
    else echo "$h ${sgn:-signed-char}: FAILED"; echo "$out" | grep FAILURE | head -5; status=1; fi
  done
done
rm -rf "$W"; exit $status
