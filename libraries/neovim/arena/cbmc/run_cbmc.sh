#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>   (pinned commit 7b87ce82)
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd); T=$(mktemp -d)
python3 -I "$D/build.py" "$1" "$T/arena.c"
cp "$D/harness.c" "$T/"
CHECKS="--bounds-check --pointer-check --pointer-overflow-check --signed-overflow-check --unsigned-overflow-check --conversion-check --undefined-shift-check --memory-leak-check --pointer-primitive-check --no-malloc-may-fail --unwinding-assertions --object-bits 16"
run() { local name=$1; shift
  for sgn in "" "--unsigned-char"; do
    if cbmc "$T/harness.c" --function harness $CHECKS $sgn "$@" > "$T/$name.log" 2>&1; then
      echo "PASS $name ${sgn:-signed-char}"
    else echo "FAIL $name ${sgn:-signed-char}"; grep -E 'FAILURE' "$T/$name.log" | head || true; fi
  done; }
run align -DH_ALIGN
run alloc -DH_ALLOC --unwind 70
run life  -DH_LIFE --unwind 6
run allocz -DH_ALLOCZ --unwind 6
for L in 0 1 4 9; do run dup$L -DH_DUP -DLEN=$L --unwind 12; done
