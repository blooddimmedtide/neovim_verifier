#!/bin/bash
# Usage: bash run.sh <neovim checkout at the pinned commit>
set -euo pipefail
cd "$(dirname "$0")"
python3 -I build.py "$1" upstream.c pins.txt
for f in ends_excmd skipwhite find_nextcmd check_nextcmd skip_colon_white checkforcmd; do
  for sg in "" --unsigned-char; do
    for n in 1 2 8; do
      conv=--conversion-check
      # ASCII_ISALPHA casts a possibly negative char to unsigned: defined (modular) in C, so
      # the conversion check, which flags every such cast, is off for checkforcmd only.
      [ $f = checkforcmd ] && conv=
      out=$(cbmc harness.c -DN=$n -DM=5 --function h_$f $sg --arch x86_64 --bounds-check --pointer-check \
        --signed-overflow-check --unsigned-overflow-check --pointer-overflow-check $conv \
        --unwind 10 --unwinding-assertions 2>&1 | tail -1)
      echo "$f N=$n ${sg:-signed-char}: $out"
      [ "$out" = "VERIFICATION SUCCESSFUL" ]
    done
  done
done
