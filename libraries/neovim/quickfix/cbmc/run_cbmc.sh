#!/bin/bash
# Usage: run_cbmc.sh <neovim tree> [MAXLEN]
set -uo pipefail
d=$(cd "$(dirname "$0")" && pwd); tree=$1; N=${2:-6}; U=$((N + 20))
python3 -I "$d/build.py" "$tree" "$d/quickfix_efm.c"
for sign in "" "--unsigned-char"; do
  for L in $(seq 0 $N); do for f in check_part_len check_analyze_prefix check_to_regpat; do
    echo "== $f LEN=$L $sign"
    cbmc "$d/harness.c" -I "$d" -DLEN=$L --function $f $sign --arch x86_64 \
      --bounds-check --pointer-check --signed-overflow-check --unsigned-overflow-check \
      --conversion-check --pointer-overflow-check --undefined-shift-check \
      --unwind $U --unwinding-assertions --object-bits 12 --slice-formula | tail -1
  done
  done
done
