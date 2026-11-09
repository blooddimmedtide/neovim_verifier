#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>   Exit 0 = every harness proved (both char signednesses).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d)
python3 -I "$HERE/build.py" "$1" "$W/menu_ext.c" || exit 1
if grep -n '__CPROVER_assume' "$W/menu_ext.c"; then echo "assume in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for h in h_winbar h_popup h_toolbar h_menubar h_separator h_hidden h_namecmp h_skip_part; do
  out=$(cbmc "$HERE/harness.c" --function $h -I "$HERE" -DMENU_C="\"$W/menu_ext.c\"" -DN=${N:-12} \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --signed-overflow-check --unsigned-overflow-check --undefined-shift-check \
        --unwind $(( ${N:-12} + 2 )) --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|rror' | head -5; status=1; fi
done; done
rm -rf "$W"; exit $status
