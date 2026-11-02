#!/bin/bash
# CBMC: the garray.c tool patches are identical to the original code. Exit 0 = all hold.
set -u; HERE=$(cd "$(dirname "$0")" && pwd); status=0
for sign in "" "--unsigned-char"; do
  cbmc "$HERE/append_store.c" $sign --bounds-check --pointer-check --unwind 6 --unwinding-assertions \
    > /tmp/ga_equiv.log 2>&1 && echo "append_store ${sign:-signed-char}: VERIFICATION SUCCESSFUL" \
    || { echo "append_store ${sign:-signed-char}: FAILED"; tail -20 /tmp/ga_equiv.log; status=1; }
done
exit $status
