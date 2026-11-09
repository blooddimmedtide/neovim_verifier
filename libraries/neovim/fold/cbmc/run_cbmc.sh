#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>. Exit 0 = every harness proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/extract.py" "$NV" "$W/fold_find.c" || exit 1
if grep -n '__CPROVER_assume' "$W/fold_find.c"; then echo "assume in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for h in h_foldFind h_foldReverseOrder; do
for n in 0 1 2 3 4 5 6; do
  out=$(cbmc "$HERE/harness.c" --function "$h" -I "$HERE" -DFOLD_FIND_C="\"$W/fold_find.c\"" -DN=$n \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --signed-overflow-check --undefined-shift-check --unwind $((n + 2)) --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h n=$n ($sign): proved"
  else echo "$h n=$n ($sign): FAILED"; echo "$out" | grep -E 'FAILURE' | head -5; status=1; fi
done; done; done
rm -rf "$W"; exit $status
