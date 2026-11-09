#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>. Exit 0 = every harness proved, both char signednesses.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/build.py" "$NV" "$W/m.c" || exit 1
if grep -n '__CPROVER_assume' "$W/m.c"; then echo "assume in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for h in h_charinfo_impl h_charinfo_impl_long h_cptr2char_adv h_cptr2char_adv_long h_safe_read; do
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(cbmc "$HERE/harness.c" --function "$h" -I "$HERE" -DMBYTE_UTF8_C="\"$W/m.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
        --undefined-shift-check --unwind 10 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -5; status=1; fi
done; done
rm -rf "$W"; exit $status
