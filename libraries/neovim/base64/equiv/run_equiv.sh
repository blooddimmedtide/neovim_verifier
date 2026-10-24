#!/bin/bash
# Usage: bash run_equiv.sh <neovim checkout>
# Each equiv_<patch>.c proves with CBMC, for every input, that a tool patch in
# ../wp/tool_patches.py computes exactly what the original statement does.
# Runs under both htobe64 implementations base64.c can be built with.
# The harnesses are regenerated first and must match the committed copies.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); status=0
G=$(mktemp -d); python3 -I "$HERE/../wp/tool_patches.py" harnesses "$NV" "$G"
for f in "$G"/*.c; do cmp -s "$f" "$HERE/$(basename "$f")" || { echo "stale: $(basename "$f")"; status=1; }; done
for f in "$HERE"/equiv_*.c; do
  for cfg in "" "-DHAVE_BE64TOH -DENDIAN_INCLUDE_FILE=<endian.h>"; do
    out=$(cbmc "$f" --function harness -I "$HERE/../cbmc/stubs" -I "$HERE/../wp/stubs" -I "$NV/src" \
          -DNVIM_BASE64_C="\"$NV/src/nvim/base64.c\"" $cfg \
          --unwinding-assertions --bounds-check --pointer-check --conversion-check 2>&1)
    if grep -q "VERIFICATION SUCCESSFUL" <<<"$out" && ! grep -q "__CPROVER_assume" "$f"; then
      echo "PROVED  $(basename "$f") ${cfg:-[vim_htobe]}"
    else echo "FAILED  $(basename "$f") ${cfg:-[vim_htobe]}"; status=1; fi
  done
done
exit $status
