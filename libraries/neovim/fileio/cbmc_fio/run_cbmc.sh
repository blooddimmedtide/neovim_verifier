#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> [fio.c]   Exit 0 = both harnesses proved, both char signednesses.
set -u; HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d); st=0
if [ $# -ge 2 ]; then cp "$2" "$W/fio.c"; else python3 -I "$HERE/build.py" "$1" "$W/fio.c" >/dev/null || exit 1; fi
for h in h_get_fio_flags h_need_conversion; do for s in signed --unsigned-char; do
  if cbmc "$HERE/harness.c" --function $h -DFIO_C="\"$W/fio.c\"" --arch x86_64 ${s#signed} --bounds-check --pointer-check \
     --signed-overflow-check --unwind 6 --unwinding-assertions 2>&1 | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($s): proved"; else echo "$h ($s): FAILED"; st=1; fi
done; done; rm -rf "$W"; exit $st
