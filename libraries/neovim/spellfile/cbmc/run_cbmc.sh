#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> [prebuilt file, used by run_mutants.sh]. Exit 0 = every harness proved, both char signednesses.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
if [ $# -ge 2 ]; then cp "$2" "$W/spellfile_read.c"; else python3 -I "$HERE/build.py" "$NV" "$W/spellfile_read.c" "$HERE/reviewed.sha256" || exit 1; fi
if grep -n '__CPROVER_assume' "$W/spellfile_read.c" | grep -v read_string_contract; then echo "assume in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for h in h_magic h_cnt_string h_region; do
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(cbmc "$HERE/harness.c" --function "$h" -I "$HERE" -DSPELLFILE_C="\"$W/spellfile_read.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --signed-overflow-check --unsigned-overflow-check --undefined-shift-check \
        --memory-leak-check --unwind 24 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -8; status=1; fi
done
# read_cnt_string for every file length (<= 70000 > 2 + 65535, so every count), on read_string's
# WP-proved contract (../wp/run_wp.sh must also pass).
  if [ -z "${ONLY:-}" ] || [[ h_cnt_string_all =~ ${ONLY} ]]; then
  out=$(cbmc "$HERE/harness_composed.c" --function h_cnt_string_all -I "$HERE" -DSPELLFILE_C="\"$W/spellfile_read.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --signed-overflow-check --unsigned-overflow-check --undefined-shift-check \
        --memory-leak-check --unwind 4 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "h_cnt_string_all ($sign): proved"
  else echo "h_cnt_string_all ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -8; status=1; fi
  fi
done
rm -rf "$W"; exit $status
