#!/bin/bash
# Usage: bash run_difftest.sh <path/to/fzf.c> [iterations-per-seed] [seeds]
# Builds the differential test with gcc -O2 + ASan/UBSan against the given
# fzf.c (fzf.h from the same directory) and runs it on several seeds.
# Exit 0: no mismatch and v2 independent of slab contents; 2: only the
# stale-slab difference (findings/v2-stale-slab-and-other-findings.md); 1: mismatch.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
F=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
IT=${2:-200000}; SEEDS=${3:-"1 2 3 4"}
W=$(mktemp -d)
gcc -O2 -g -fsanitize=address,undefined -fno-sanitize-recover=all -Wall -Wno-unused-function \
  -I "$HERE/../cbmc" -I "$(dirname "$F")" -DFZF_C="\"$F\"" "$HERE/difftest.c" -o "$W/dt" || exit 1
gcc -O2 -Wall -Wno-stringop-truncation -fno-builtin -I "$HERE/../cbmc" "$HERE/libc_check.c" -o "$W/lc" || exit 1
"$W/lc" || exit 1
st=0
for s in $SEEDS; do
  echo "seed $s:"; "$W/dt" "$IT" "$s"; r=$?
  [ $r -eq 1 ] && st=1; [ $r -eq 2 ] && [ $st -eq 0 ] && st=2
  [ $r -gt 2 ] && st=1
done
rm -rf "$W"; exit $st
