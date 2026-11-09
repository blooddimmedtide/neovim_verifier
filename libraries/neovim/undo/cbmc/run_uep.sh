#!/bin/bash
# Usage: bash run_uep.sh <neovim checkout>   BOUNDED proof of unserialize_uep / serialize_uep
# (ue_size <= UEP_MAX=2 lines of <= 2 bytes). Exit 0 = both harnesses proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/build_uep.py" "$NV" "$W/uep.c" || exit 1
status=0
for sign in signed --unsigned-char; do
for h in h_unserialize_uep h_uep_roundtrip; do
  out=$(timeout 1200 cbmc "$HERE/harness_uep.c" --function $h -I "$HERE" -DUNDO_IO_C="\"$W/uep.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --signed-overflow-check --undefined-shift-check --memory-leak-check --object-bits 10 \
        --unwind 40 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E ": FAILURE$|error:|too many|Killed|out of memory" | head -8; echo "$out" | tail -2; status=1; fi
done; done
rm -rf "$W"; exit $status
