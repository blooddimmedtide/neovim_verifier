#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> [mbyte_utf8.c to use instead of building one]
# Full-correctness proof of the UTF-8 helpers of src/nvim/mbyte.c with CBMC.
# Works on upstream and on the fixed fork (build.py detects the fixed utf_cp_bounds_len).
# ONLY=<regex> limits the run to matching harness names (used by run_mutants.py).
# Exit 0 = every harness proved, with all bounds proved enough.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d)
if [ $# -ge 2 ]; then cp "$2" "$W/mbyte_utf8.c"; else python3 -I "$HERE/build.py" "$NV" "$W/mbyte_utf8.c" || exit 1; fi
if grep -n '__CPROVER_assume' "$W/mbyte_utf8.c"; then echo "assume in code under test"; exit 1; fi
status=0
# x86_64 with signed char (Neovim's build), then unsigned char (e.g. arm64 Linux).
for sign in signed --unsigned-char; do
for hf in harness.c:h_byte2len harness.c:h_char2len harness.c:h_char2bytes harness.c:h_ptr2len \
          harness.c:h_ptr2len_long harness.c:h_ptr2char harness.c:h_ptr2char_long harness.c:h_ptr2len_len \
          harness_bounds.c:h_cp_bounds_len harness_bounds.c:h_cp_bounds; do
  f=${hf%%:*}; h=${hf#*:}
  # The bounds harnesses take distances up to 2^60, so give pointers 61 offset bits.
  ob=""; [ "$f" = harness_bounds.c ] && ob="--object-bits 3"
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(cbmc "$HERE/$f" --function "$h" -I "$HERE" -DMBYTE_UTF8_C="\"$W/mbyte_utf8.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
        --undefined-shift-check $ob --unwind 10 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE' | head -5; status=1; fi
done
done
rm -rf "$W"; exit $status
