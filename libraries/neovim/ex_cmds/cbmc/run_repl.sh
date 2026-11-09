#!/bin/bash
# Usage: bash run_repl.sh <neovim checkout>. Exit 0 = proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/build_repl.py" "$NV" "$W/r.c" || exit 1
status=0
for sign in signed --unsigned-char; do
  out=$(cbmc "$HERE/harness_repl.c" --function h_set_get -I "$HERE" -DREPL_C="\"$W/r.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --memory-leak-check --pointer-primitive-check --unwind 3 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "sub_set/get_replacement ($sign): proved"
  else echo "sub_set/get_replacement ($sign): FAILED"; echo "$out" | grep -E ': FAILURE$|error' | head -5; status=1; fi
done
rm -rf "$W"; exit $status
