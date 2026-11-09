#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> [bom.c]   Exit 0 = proved for both char signednesses.
set -u; HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d); status=0
if [ $# -ge 2 ]; then cp "$2" "$W/bom.c"; else python3 -I "$HERE/build.py" "$1" "$W/bom.c" >/dev/null || exit 1; fi
for s in signed --unsigned-char; do
  if cbmc "$HERE/harness.c" --function h_check_for_bom -I "$HERE" -DFILEIO_BOM_C="\"$W/bom.c\"" --arch x86_64 ${s#signed} \
     --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check --unwind 12 --unwinding-assertions 2>&1 | grep -q "VERIFICATION SUCCESSFUL"
  then echo "check_for_bom ($s): proved"; else echo "check_for_bom ($s): FAILED"; status=1; fi
done; rm -rf "$W"; exit $status
