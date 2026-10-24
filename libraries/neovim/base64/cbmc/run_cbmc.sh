#!/bin/bash
# Usage: run_cbmc.sh <neovim-src-dir> <harness-name> <len>
# Runs one CBMC proof for one exact input length. Exit 0 = proved.
# --conversion-check is left out on purpose: it flags (char)(int 128..255) in
# base64_decode, which is implementation-defined (wraps on gcc/clang), not UB.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
NV=$1; H=$2; L=$3
UNWIND=$(( L * 2 + 10 ))
cd "$HERE"
exec cbmc --function harness -I stubs -I . \
  --bounds-check --pointer-check --memory-leak-check \
  --signed-overflow-check --unsigned-overflow-check --pointer-overflow-check \
  --undefined-shift-check --div-by-zero-check \
  --unwinding-assertions --unwind "$UNWIND" -DEXACT_LEN="$L" \
  "${H}_harness.c" "$NV/src/nvim/base64.c"
