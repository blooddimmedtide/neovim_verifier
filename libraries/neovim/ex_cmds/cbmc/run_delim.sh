#!/bin/bash
# Usage: bash run_delim.sh <neovim checkout>. Exit 0 = every harness proved.
# h_call_sites fails on upstream (signed char) by design: it is the finding. ONLY=<regex> limits harnesses.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d)
python3 -I "$HERE/build_delim.py" "$NV" "$W/d.c" || exit 1
status=0
for sign in signed --unsigned-char; do for h in h_check_regexp_delim h_call_sites; do
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(cbmc "$HERE/harness_delim.c" --function $h -I "$HERE" -D__NO_CTYPE -DDELIM_C="\"$W/d.c\"" \
        --arch x86_64 ${sign#signed} --bounds-check --pointer-check --signed-overflow-check \
        --unwind 8 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E ': FAILURE$|error' | head -5; status=1; fi
done; done
rm -rf "$W"; exit $status
