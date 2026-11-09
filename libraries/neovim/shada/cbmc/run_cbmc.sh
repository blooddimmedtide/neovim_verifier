#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> [shada_read.c to use instead of building one]
# Full-correctness proof of the ShaDa reading primitives of src/nvim/shada.c with CBMC.
# ONLY=<regex> limits the run to matching harness names (used by run_mutants.py).
# Exit 0 = every harness proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d)
if [ $# -ge 2 ]; then cp "$2" "$W/shada_read.c"; else python3 -I "$HERE/build.py" "$NV" "$W/shada_read.c" || exit 1; fi
if grep -n '__CPROVER_assume' "$W/shada_read.c"; then echo "assume in code under test"; exit 1; fi
status=0
# x86_64 with signed char (Neovim's build), then unsigned char (e.g. arm64 Linux).
for sign in signed --unsigned-char; do
for h in h_be64toh h_read_uint64 h_fread_len h_skip h_check_status; do
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(cbmc "$HERE/harness.c" --function "$h" -I "$HERE" -DSHADA_READ_C="\"$W/shada_read.c\"" \
        --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
        --conversion-check --signed-overflow-check --unsigned-overflow-check \
        --undefined-shift-check --unwind 16 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($sign): proved"
  else echo "$h ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -8; status=1; fi
done
done
rm -rf "$W"; exit $status
