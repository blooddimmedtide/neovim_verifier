#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> <upstream|fixed>
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); MODE=$2; status=0
W=$(mktemp -d); cp "$HERE/harness.c" "$HERE"/../wp/stubs/*.h "$W/"
python3 -I "$HERE/../wp/build.py" "$NV" "$W/mt.c" "$MODE" || exit 1
for f in check_meta_describe_key_inc check_meta_describe_key check_meta_has; do
  for d in "" "-D DOC_FILTER"; do
    [ "$f" != check_meta_has ] && [ -n "$d" ] && continue
    for sg in "" "--unsigned-char"; do
      out=$(cd "$W" && cbmc harness.c -I . $d $sg --function $f --unwind 7 --unwinding-assertions \
            --bounds-check --pointer-check --signed-overflow-check --conversion-check --undefined-shift-check 2>&1)
      r=$(echo "$out" | grep -E "VERIFICATION (SUCCESSFUL|FAILED)")
      echo "$MODE $f $d $sg: ${r:-no result}"
      echo "$r" | grep -q SUCCESSFUL || { status=1; echo "$out" | grep -E "FAILURE" | head -5; }
    done
  done
done
exit $status
