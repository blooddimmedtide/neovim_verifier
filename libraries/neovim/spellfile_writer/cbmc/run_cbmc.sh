#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>. Needs cbmc 6.11.0.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); bash "$here/../exhaustive/extract.sh" "$1"
for s in "" "--unsigned-char"; do
  cbmc $s --bounds-check --pointer-check --signed-overflow-check --unsigned-overflow-check \
    --undefined-shift-check --memory-leak-check --unwind 6 --unwinding-assertions "$here/harness.c"
done
