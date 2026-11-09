#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>. Full-correctness proofs of grid.c schar helpers.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/build.py" "$NV" "$W/grid.c" ${SKIP_PINS:-} || exit 1
if grep -n '__CPROVER' "$W/grid.c"; then echo "CPROVER in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for h in ${HARNESSES:-h_schar_high h_schar_get_ascii h_schar_len h_schar_get_adv h_schar_get \
         h_schar_get_first_byte h_schar_in_arabic_block h_schar_from_char h_grid_adjust h_grid_invalid_row h_grid_getchar h_grid_line_getchar h_grid_line_put_schar h_grid_line_cursor_goto}; do
  out=$(cbmc "$HERE/harness.c" --function "$h" -I "$HERE" -DGRID_C="\"$W/grid.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --signed-overflow-check --undefined-shift-check \
        --unwind 42 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -6; status=1; fi
done; done
rm -rf "$W"; exit $status
