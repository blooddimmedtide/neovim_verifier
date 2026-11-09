#!/bin/bash
# Usage: bash probes.sh <dir holding strbuf.c and strbuf.h>
# Runs the reviewer probes in probes.c; prints each verdict and the expected one.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); SRC=$(cd "$1" && pwd)
F=(-I "$HERE/../cbmc" -I "$SRC" -DSTRBUF_C="\"$SRC/strbuf.c\"" --arch x86_64 --bounds-check --pointer-check
   --signed-overflow-check --conversion-check --sat-solver cadical)
for c in c_free_to_string:4 c_append_string:8 c_helpers:8 c_resize:66 c_cns:66 c_init:66; do
  h=${c%%:*}; u=${c#*:}
  echo "== $h (FAILED = unreachable)"
  cbmc "$HERE/probes.c" --function "$h" "${F[@]}" --unwind "$u" --cover cover 2>&1 | grep "function $h " | sed 's/.*line \([0-9]*\) function [^ ]* /  line \1: /'
done
for q in q_reallocs_max:66:FAILED q_resize_no_growth:66:SUCCESSFUL q_ensure_wrap:66:FAILED \
         q_uaf_unseen:4:SUCCESSFUL q_realloc_stale:4:SUCCESSFUL q_cns_wide:66:SUCCESSFUL; do
  IFS=: read h u want <<< "$q"
  got=$(cbmc "$HERE/probes.c" --function "$h" "${F[@]}" --unwind "$u" --unwinding-assertions 2>&1 | grep -o 'VERIFICATION [A-Z]*' | cut -d' ' -f2)
  echo "$h: $got (expected $want)"
done
