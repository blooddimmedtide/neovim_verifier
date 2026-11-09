#!/bin/bash
# Usage: bash run.sh [-DFIXED] [-DCHECK_CHAR -DCHECK_IDX -DCHECK_DEL]
O="--bounds-check --pointer-check --signed-overflow-check --unwinding-assertions --unwind 10"
for hl in 0 1 2 3 4; do
  echo "== hislen=$hl $*"; cbmc harness.c -DN=4 -DHL=$hl "$@" $O 2>&1 | grep -E "FAILURE|^VERIFICATION" | sort | uniq -c
done
