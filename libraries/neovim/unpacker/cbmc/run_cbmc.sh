#!/bin/bash
# Usage: [MODE=fixed] bash run_cbmc.sh <neovim checkout> [unpacker_part.c to use instead of building one]
# Full-correctness proof of the loop-free token readers of src/nvim/msgpack_rpc/unpacker.c
# with CBMC (real mpack reader included, no stubs). Exit 0 = every harness proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d)
if [ $# -ge 2 ]; then cp "$2" "$W/unpacker_part.c"; else python3 -I "$HERE/build.py" "$NV" "$W/unpacker_part.c" "${MODE:-upstream}" || exit 1; fi
python3 -I "$HERE/build_init.py" "$NV" "$W/init_part.c" || exit 1
if grep -n '__CPROVER_assume' "$W/unpacker_part.c" "$W/init_part.c"; then echo "assume in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
for hf in harness.c:h_unpack_string harness.c:h_unpack_array harness.c:h_unpack_integer harness.c:h_unpack_uint_or_sint \
          harness.c:h_parse_nop harness.c:h_api_parse_exit harness_ad.c:h_push_additional_data harness_init.c:h_unpacker_init; do
  f=${hf%%:*}; h=${hf#*:}
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(cbmc "$HERE/$f" --function "$h" -I "$HERE" -I "$HERE/stubs" -I "$NV/src" -I "$NV/src/mpack" -DUNPACKER_C="\"$W/unpacker_part.c\"" -DINIT_C="\"$W/init_part.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
        --undefined-shift-check --pointer-overflow-check --object-bits 8 \
        --unwind 40 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "${MODE:-upstream} $h ($sign): proved"
  else echo "${MODE:-upstream} $h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -8; status=1; fi
done
done
rm -rf "$W"; exit $status
