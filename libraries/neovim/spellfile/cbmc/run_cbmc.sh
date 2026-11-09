#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> [prebuilt file, used by run_mutants.sh]. Exit 0 = every harness proved, both char signednesses.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
if [ $# -ge 2 ]; then cp "$2" "$W/spellfile_read.c"; else python3 -I "$HERE/build.py" "$NV" "$W/spellfile_read.c" "$HERE/reviewed.sha256" || exit 1; fi
if grep -n '__CPROVER_assume' "$W/spellfile_read.c"; then echo "assume in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for h in ${ONLY:-h_magic h_cnt_string h_region}; do
  out=$(cbmc "$HERE/harness.c" --function "$h" -I "$HERE" -DSPELLFILE_C="\"$W/spellfile_read.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --signed-overflow-check --unsigned-overflow-check --undefined-shift-check \
        --memory-leak-check --unwind 24 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -8; status=1; fi
done; done
rm -rf "$W"; exit $status
