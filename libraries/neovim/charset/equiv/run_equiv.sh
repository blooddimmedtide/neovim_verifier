#!/bin/bash
# Usage: bash run_equiv.sh <neovim checkout> [L] [--fixed]
# CBMC: the goto-free rewrite of backslash_halve (wp/tool_patches.py) leaves the same
# bytes as the upstream function, for every buffer of L bytes plus a NUL (every string
# of length <= L), with signed and unsigned char. Exit 0 = both runs verified.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); L=${2:-12}; FIX=${3:-}
W=$(mktemp -d); status=0
python3 -I "$HERE/gen_equiv.py" "$NV" "$W/equiv.c" || exit 1
for sign in "" --unsigned-char; do
  cbmc "$W/equiv.c" --function harness -DL=$L $sign --unwind $((L + 3)) --unwinding-assertions \
    --bounds-check --pointer-check --signed-overflow-check --no-malloc-may-fail > "$W/cbmc$sign.log" 2>&1
  r=$(tail -1 "$W/cbmc$sign.log"); echo "equiv backslash_halve L=$L ${sign:-signed-char}: $r"
  [ "$r" = "VERIFICATION SUCCESSFUL" ] || status=1
done
# vim_str2nr: the macro expansion, condition flattening and loop outlining (wp/tool_patches.py)
# store the same results as the real function, for every string of length <= LS.
LS=$(( L < 6 ? L : 6 ))
python3 -I "$HERE/gen_equiv_str2nr.py" "$NV" "$W/equiv_s.c" $FIX || exit 1
for sign in "" --unsigned-char; do
  cbmc "$W/equiv_s.c" --function harness -DL=$LS $sign --unwind $((LS + 3)) --unwinding-assertions \
    --bounds-check --pointer-check --signed-overflow-check > "$W/cbmc_s$sign.log" 2>&1
  r=$(tail -1 "$W/cbmc_s$sign.log"); echo "equiv vim_str2nr L=$LS ${sign:-signed-char}: $r"
  [ "$r" = "VERIFICATION SUCCESSFUL" ] || status=1
done
exit $status
