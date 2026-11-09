#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>   Exit 0 = every harness proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/build.py" "$NV" "$W/sub.c" || exit 1
status=0
for sign in signed --unsigned-char; do
  out=$(cbmc "$HERE/harness.c" --function h_sub_parse_flags -I "$HERE" -DSUB_C="\"$W/sub.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --signed-overflow-check --undefined-shift-check --unwind 11 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "sub_parse_flags ($sign): proved"
  else echo "sub_parse_flags ($sign): FAILED"; echo "$out" | grep -E ': FAILURE$|error' | head -5; status=1; fi
done
rm -rf "$W"; exit $status
