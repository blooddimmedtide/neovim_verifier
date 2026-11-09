#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>   (exit 0 = all proved)
set -u; HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d); status=0
bash "$HERE/build.sh" "$1" "$W/env_part.c" || exit 1
for sign in signed --unsigned-char; do for h in h_iter h_iter_rev; do
  out=$(cbmc "$HERE/harness.c" -DENV_C="\"$W/env_part.c\"" -DN=${N:-4} --function $h --arch x86_64 ${sign#signed} \
        --bounds-check --pointer-check --signed-overflow-check --unsigned-overflow-check \
        --pointer-overflow-check --conversion-check --memory-leak-check --no-malloc-may-fail \
        --unwind $(( ${N:-4} + 3 )) --unwinding-assertions 2>&1)
  r=$(echo "$out" | grep -E 'VERIFICATION (SUCCESSFUL|FAILED)')
  echo "$h ${sign}: $r"; [[ $r == *SUCCESSFUL* ]] || { status=1; echo "$out" | grep -E 'FAILURE' | head; }
done; done; exit $status
