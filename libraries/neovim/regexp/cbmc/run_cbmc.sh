#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>
# Full-correctness proof of regexp.c's gethexchrs and getoctchrs with CBMC, for
# both char signednesses on x86_64. Exit 0 = every harness proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d)
python3 -I "$HERE/build.py" "$NV" "$W/regexp_num.c" || exit 1
if grep -n '__CPROVER_assume' "$W/regexp_num.c"; then echo "assume in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for h in ${ONLY:-h_gethexchrs h_getoctchrs}; do
  out=$(cbmc "$HERE/harness.c" --function "$h" -I "$HERE" -DREGEXP_NUM_C="\"$W/regexp_num.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
        --undefined-shift-check --unwind 10 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -5; status=1; fi
done
done
rm -rf "$W"; exit $status
