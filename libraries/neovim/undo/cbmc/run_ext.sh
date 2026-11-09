#!/bin/bash
# Usage: bash run_ext.sh <neovim checkout> [prebuilt ext.c]   CBMC proof of serialize_extmark, unserialize_extmark
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
if [ $# -ge 2 ]; then cp "$2" "$W/ext.c"; else python3 -I "$HERE/build_ext.py" "$NV" "$W/ext.c" || exit 1; fi
status=0
for sign in signed --unsigned-char; do
for h in h_serialize_extmark h_serialize_extmark_ok h_unserialize_extmark; do
  out=$(timeout 600 cbmc "$HERE/harness_ext.c" --function $h -I "$HERE" -DUNDO_IO_C="\"$W/ext.c\"" --arch x86_64 ${sign#signed} \
        --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check --undefined-shift-check \
        --memory-leak-check --unwind 70 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E ": FAILURE$|error:" | head -5; status=1; fi
done; done
rm -rf "$W"; exit $status
