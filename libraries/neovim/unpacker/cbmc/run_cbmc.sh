#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> [unpacker_part.c to use instead of building one]
# Full-correctness proof of the loop-free token readers of src/nvim/msgpack_rpc/unpacker.c
# with CBMC (real mpack reader included, no stubs). Exit 0 = every harness proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d)
if [ $# -ge 2 ]; then cp "$2" "$W/unpacker_part.c"; else python3 -I "$HERE/build.py" "$NV" "$W/unpacker_part.c" || exit 1; fi
if grep -n '__CPROVER_assume' "$W/unpacker_part.c"; then echo "assume in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for h in h_unpack_string h_unpack_array h_unpack_integer h_unpack_uint_or_sint h_parse_nop; do
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(cbmc "$HERE/harness.c" --function "$h" -I "$HERE" -I "$NV/src/mpack" -DUNPACKER_C="\"$W/unpacker_part.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
        --undefined-shift-check --pointer-overflow-check --object-bits 8 \
        --unwind 10 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -8; status=1; fi
done
done
rm -rf "$W"; exit $status
