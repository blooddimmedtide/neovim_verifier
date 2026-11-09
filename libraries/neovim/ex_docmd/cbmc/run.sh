#!/bin/bash
# Usage: bash run.sh <neovim checkout at the pinned commit>
set -euo pipefail
cd "$(dirname "$0")"
python3 -I build.py "$1" upstream.c pins.txt
for f in ends_excmd skipwhite skipdigits find_nextcmd check_nextcmd skip_colon_white checkforcmd modifier_len parse_bang one_letter_cmd; do
  for sg in "" --unsigned-char; do
    sizes="1 2 8"
    # 14 bytes hold the longest modifier name (keeppatterns) with a count, blank and tail.
    [ $f = modifier_len ] && sizes="1 2 8 14"
    for n in $sizes; do
      conv=--conversion-check
      # ASCII_ISALPHA casts a possibly negative char to unsigned: defined (modular) in C, so
      # the conversion check, which flags every such cast, is off for checkforcmd and modifier_len.
      case $f in checkforcmd|modifier_len) conv= ;; esac
      out=$(cbmc harness.c -DN=$n -DM=5 --function h_$f $sg --arch x86_64 --bounds-check --pointer-check \
        --signed-overflow-check --unsigned-overflow-check --pointer-overflow-check $conv \
        --unwind 30 --unwinding-assertions 2>&1 | tail -1)
      echo "$f N=$n ${sg:-signed-char}: $out"
      [ "$out" = "VERIFICATION SUCCESSFUL" ]
    done
  done
done
