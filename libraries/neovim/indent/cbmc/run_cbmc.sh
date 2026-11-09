#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>   (ONLY=<regex> limits harnesses)
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/extract.py" "$NV" "$W/indent_tabstop.c" || exit 1
if grep -n '__CPROVER_assume' "$W/indent_tabstop.c"; then echo "assume in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for h in h_padding h_at h_start h_fromto h_copy_count_first; do
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(timeout ${TMO:-900} cbmc "$HERE/harness.c" --function $h -I "$HERE" -DINDENT_C="\"$W/indent_tabstop.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
        --div-by-zero-check --undefined-shift-check --conversion-check --unwind 6 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -5; status=1; fi
done; done
rm -rf "$W"; exit $status
