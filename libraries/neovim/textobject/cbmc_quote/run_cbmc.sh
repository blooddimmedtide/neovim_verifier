#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>   Exit 0 = both harnesses proved, both signednesses.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/extract.py" "$NV" "$W/quote.c" >/dev/null || exit 1
status=0
for sign in ${SIGNS:-signed --unsigned-char}; do for h in h_next h_prev; do
  # h_prev has two nested loops; line length 4 keeps it near one minute.
  lim="-DLMAX=6 --unwind 9"; [ $h = h_prev ] && lim="-DLMAX=4 --unwind 7"
  out=$(cbmc "$HERE/harness.c" --function $h -I "$HERE" -DQUOTE_C="\"$W/quote.c\"" ${CBMC_EXTRA:-} \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --signed-overflow-check $lim --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|ERROR|error' | head -5; status=1; fi
done; done
rm -rf "$W"; exit $status
