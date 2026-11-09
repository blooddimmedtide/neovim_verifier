#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> [undo_io.c to use instead of building one]
# Full-correctness proof of the undo-file byte helpers (src/nvim/undo.c, get*c of fileio.c).
# ONLY=<regex> limits the run to matching harness names. Exit 0 = every harness proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d)
if [ $# -ge 2 ]; then cp "$2" "$W/undo_io.c"; else python3 -I "$HERE/build.py" "$NV" "$W/undo_io.c" || exit 1; fi
if grep -n '__CPROVER_assume' "$W/undo_io.c"; then echo "assume in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for h in h_write_bytes h_put_header_ptr h_read_4c h_read_2c h_read_byte h_read_time h_read_len \
         h_read h_read_string h_serialize_pos h_serialize_visualinfo h_unserialize_pos \
         h_unserialize_visualinfo h_seq_cmp; do   # uhp_table_find: ../wp (any size); h_table_find is a bounded cross-check, run with ONLY=h_table_find
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(timeout 600 cbmc "$HERE/harness.c" --function "$h" -I "$HERE" -DUNDO_IO_C="\"$W/undo_io.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --signed-overflow-check --undefined-shift-check --memory-leak-check \
        --unwind 40 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E ": FAILURE$|^.*error:" | head -8; status=1; fi
done
done
rm -rf "$W"; exit $status
