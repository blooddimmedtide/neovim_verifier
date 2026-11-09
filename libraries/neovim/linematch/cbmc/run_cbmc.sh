#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>. Bounded proofs (buffers up to N bytes, default 4).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d); N=${N:-4}
python3 -I "$HERE/build.py" "$NV" "$W/lm.c" || exit 1
status=0
for sign in signed --unsigned-char; do
for h in ${HARNESSES:-h_line_len h_fastforward h_matching_chars h_matching_chars_iwhite h_count_n}; do
  out=$(timeout ${TMO:-600} cbmc "$HERE/harness.c" --function $h -I "$HERE" -DN=$N -DLINEMATCH_C="\"$W/lm.c\"" \
     --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
     --conversion-check --unwind $((N+3)) --unwindset matching_chars.0:$((N+1)),matching_chars.1:$((N+1)) --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|unwinding' | head -6; status=1; fi
done; done
rm -rf "$W"; exit $status
