#!/bin/bash
# Usage: bash run_bridge.sh <neovim checkout>
# CBMC proof that vim_htobe64 / vim_htobe32 give the big-endian value,
# plus memory safety and termination of vim_htobe64 / vim_htobe32. Exit 0 = proved.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
cbmc --function harness -I "$HERE/../cbmc/stubs" -DNVIM_BASE64_C="\"$NV/src/nvim/base64.c\"" \
  --bounds-check --pointer-check --signed-overflow-check --unsigned-overflow-check \
  --undefined-shift-check --unwind 10 --unwinding-assertions "$HERE/bridge.c"
