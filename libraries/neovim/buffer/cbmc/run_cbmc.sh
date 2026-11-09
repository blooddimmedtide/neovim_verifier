#!/bin/bash
# Usage: bash run_cbmc.sh <path to buffer.c>
set -eu
here=$(cd "$(dirname "$0")" && pwd); cd "$here"
bash extract.sh "$1" out
F="--bounds-check --pointer-check --signed-overflow-check --conversion-check --div-by-zero-check --undefined-shift-check --pointer-overflow-check --unwinding-assertions"
for arch in "" "--unsigned-char"; do
  for h in h_calc_percentage h_buf_time_compare h_buf_time_compare_bufmatch; do
    echo "== $h $arch"; cbmc harness.c --function $h $F --arch x86_64 $arch | tail -1
  done
done
