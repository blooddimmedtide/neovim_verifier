#!/bin/bash
# Usage: bash run_cbmc.sh <path/to/fzf.c> [ONLY-regex]
# Runs every CBMC harness against the given fzf.c (fzf.h is taken from the same
# directory). The file is used unchanged; its sha256 is printed and checked
# against the two reviewed versions (upstream b25b749 and the fixed copy).
# ONLY=<regex> (or the 2nd argument) limits the run to matching harness names.
# Exit 0 = every selected harness proved (including unwinding assertions).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
F=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
ONLY=${2:-${ONLY:-}}
UPSTREAM=92dfce0d6eb3b129ef6b44ce55514b875b7763cf912f2d0047c01c489875f1e0
FIXED=b65aa7018294959645531ef569a110ac03c4a5b21742b831f6b239db053621a4
FIXED2=4db1b499e626a0223f028f34ffc21a5ddbe28bc409246a5acfb438cf30cc2f2d   # fixed + findings/fix-v2-stale-slab.diff
H=$(sha256sum "$F" | cut -d' ' -f1)
case $H in
  $UPSTREAM) echo "fzf.c = upstream b25b749 ($H)";;
  $FIXED) echo "fzf.c = fixed copy ($H)";;
  $FIXED2) echo "fzf.c = fixed copy + stale-slab fix ($H)";;
  *) echo "fzf.c = UNREVIEWED version ($H)";;
esac
if grep -n '__CPROVER' "$F"; then echo "CPROVER construct in the code under test"; exit 1; fi
# Checks: every pointer access in bounds of a live object, no signed overflow,
# no undefined shift, no NULL/freed/dead dereference; malloc never fails (the
# code does not check it); loops unwound completely (unwinding assertions).
COMMON="--unwindset memset.0:64,exact_malloc.0:52,strlen.0:16 -I $HERE -I $(dirname "$F") -D__NO_CTYPE --arch x86_64 --no-malloc-may-fail
  --bounds-check --pointer-check --signed-overflow-check --undefined-shift-check
  --pointer-primitive-check --div-by-zero-check --unwinding-assertions"
# harness-file:function:unwind[:extra flags]
LIST="
harness_helpers.c:h_char_class:2
harness_helpers.c:h_bonus_for:2
harness_helpers.c:h_small:2
harness_helpers.c:h_index_byte:8
harness_helpers.c:h_bonus_at:8
harness_helpers.c:h_whitespaces:8
harness_helpers.c:h_copy:8
harness_helpers.c:h_prefix_suffix:8
harness_helpers.c:h_str_tolower:8
harness_helpers.c:h_trim_left:8
harness_helpers.c:h_replace_char:9
harness_helpers.c:h_str_replace:9:--z3
harness_helpers.c:h_pos_array:8
harness_helpers.c:h_append_pos:8
harness_helpers.c:h_insert_range:8
harness_helpers.c:h_alloc:8
harness_helpers.c:h_ascii_fuzzy_index:8
harness_helpers.c:h_try_skip:8
$(cat "$HERE/match_list.txt" 2>/dev/null)
"
ulimit -v 6000000   # 6 GB per cbmc: the machine is shared
status=0
for e in $LIST; do
  IFS=: read -r file fn unw extra <<< "$e"
  if [ -n "$ONLY" ] && ! [[ $fn =~ $ONLY ]]; then continue; fi
  t0=$(date +%s)
  out=$(cbmc "$HERE/$file" "$HERE/libc_model.c" --function "$fn" -DFZF_C="\"$F\"" $COMMON \
        --unwind "$unw" ${extra//,/ } 2>&1)
  dt=$(( $(date +%s) - t0 ))
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$fn: proved (${dt}s)"
  else echo "$fn: FAILED (${dt}s)"; echo "$out" | grep -E "FAILURE|error|CONVERSION" | head -8; echo "$out" | tail -3; status=1; fi
done
exit $status
