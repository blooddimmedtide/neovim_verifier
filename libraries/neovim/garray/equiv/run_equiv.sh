#!/bin/bash
# CBMC: the garray.c tool patch is identical to the original code. Exit 0 = all hold.
# Signed char (the WP machdep): also checks that the patched conversion is in range.
# Unsigned char: same bytes (conversion to unsigned char is defined modulo 256, so
# --conversion-check, which flags any out-of-range value, is not used there).
set -u; HERE=$(cd "$(dirname "$0")" && pwd); status=0
for sign in "" "--unsigned-char"; do
  extra=$([ -z "$sign" ] && echo "--conversion-check" || true)
  cbmc "$HERE/append_store.c" $sign $extra --bounds-check --pointer-check --signed-overflow-check \
    --unwind 6 --unwinding-assertions > /tmp/ga_equiv.log 2>&1 \
    && echo "append_store ${sign:-signed-char}: VERIFICATION SUCCESSFUL" \
    || { echo "append_store ${sign:-signed-char}: FAILED"; grep FAIL /tmp/ga_equiv.log; status=1; }
done
exit $status
