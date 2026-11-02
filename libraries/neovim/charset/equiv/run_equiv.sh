#!/bin/bash
# Usage: bash run_equiv.sh <neovim checkout> [L]
# CBMC: the goto-free rewrite of backslash_halve (wp/tool_patches.py) leaves the same
# bytes as the upstream function, for every buffer of L bytes plus a NUL (every string
# of length <= L), with signed and unsigned char. Exit 0 = both runs verified.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); L=${2:-12}
W=$(mktemp -d); status=0
python3 -I "$HERE/gen_equiv.py" "$NV" "$W/equiv.c" || exit 1
for sign in "" --unsigned-char; do
  cbmc "$W/equiv.c" --function harness -DL=$L $sign --unwind $((L + 3)) --unwinding-assertions \
    --bounds-check --pointer-check --signed-overflow-check --no-malloc-may-fail > "$W/cbmc$sign.log" 2>&1
  r=$(tail -1 "$W/cbmc$sign.log"); echo "equiv backslash_halve L=$L ${sign:-signed-char}: $r"
  [ "$r" = "VERIFICATION SUCCESSFUL" ] || status=1
done
exit $status
