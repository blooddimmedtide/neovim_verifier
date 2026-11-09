#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout at the pin>. Checks the verbatim copy, then proves it.
set -eu; H=$(cd "$(dirname "$0")" && pwd)
sed -n '/^static inline uint64_t mt_dbg_id/,/^}/p' "$1/src/nvim/marktree.c" > /tmp/up.c
sed -n '/^static inline uint64_t mt_dbg_id/,/^}/p' "$H/harness.c" | diff - /tmp/up.c
for s in "" "--unsigned-char"; do cbmc "$H/harness.c" $s --function check_dbg_id --bounds-check --signed-overflow-check --conversion-check --undefined-shift-check | grep -q "VERIFICATION SUCCESSFUL"; echo "check_dbg_id $s: OK"; done
