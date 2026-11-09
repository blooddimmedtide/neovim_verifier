#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>   Exit 0 = every harness verified (both char signednesses).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d); status=0
python3 -I "$HERE/../wp/build.py" "$NV" "$W/ro.c" || exit 1
cp "$HERE/harness.c" "$W/"
if grep -n "__CPROVER_assume" "$W/ro.c"; then echo "assume in extracted code"; exit 1; fi
for cs in "" "--unsigned-char"; do
  for h in harness_get_unname_register harness_op_reg_iter; do
    (cd "$W" && cbmc harness.c --function "$h" $cs --bounds-check --pointer-check --signed-overflow-check \
       --unsigned-overflow-check --pointer-overflow-check --conversion-check --undefined-shift-check \
       --unwind 45 --unwinding-assertions --no-malloc-may-fail > "$h$cs.log" 2>&1)
    r=$(grep -E "VERIFICATION (SUCCESSFUL|FAILED)" "$W/$h$cs.log"); echo "$h ${cs:-signed}: ${r:-no result}"
    [ "$r" = "VERIFICATION SUCCESSFUL" ] || { status=1; grep -E "FAILURE" "$W/$h$cs.log" | head; }
  done
done
echo "logs: $W"; exit $status
