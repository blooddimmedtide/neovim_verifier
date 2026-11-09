#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout at the pinned commit> [NAMELEN]
# find_special_key_in_table: every int. With NAMELEN (17 = one more than the longest key
# name) also get_special_key_code on every name of NAMELEN bytes followed by NUL.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d); status=0
bash "$HERE/gen.sh" "$NV" "$W" && python3 -I "$HERE/build.py" "$NV" "$W" || exit 1
cp "$HERE/harness.c" "$W/"
OPTS="--bounds-check --pointer-check --signed-overflow-check --unwind 200 --unwinding-assertions"
for sign in "" --unsigned-char; do
  TS=("-D IN_TABLE"); [ -n "${2:-}" ] && TS+=("-D NAMELEN=$2")   # get_special_key_code: not yet proved
  for t in "${TS[@]}"; do
    r=$(cd "$W" && cbmc harness.c $t $sign $OPTS 2>&1 | grep '^VERIFICATION')
    echo "$t ${sign:-signed}: $r"; [ "$r" = "VERIFICATION SUCCESSFUL" ] || status=1
  done
done
exit $status
