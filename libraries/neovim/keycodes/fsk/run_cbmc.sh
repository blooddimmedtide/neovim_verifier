#!/bin/bash
# Usage: bash run_cbmc.sh <upstream tree> <fixed tree> [LEN]
# INT_MIN property of find_special_key on every source of LEN bytes (default 8, the length
# of "<Char-1>"; the stubbed vim_str2nr returns any number, so longer digit strings add no
# behavior). Expected: upstream FAILED (the finding), fixed SUCCESSFUL.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d); status=0
bash "$HERE/../table/gen.sh" "$1" "$W" && python3 -I "$HERE/../table/build.py" "$1" "$W" || exit 1
for v in up fix; do
  tree=$1; [ $v = fix ] && tree=$2; mkdir -p "$W/$v"
  python3 -I "$HERE/build.py" "$tree" "$W" "$W/$v/fsk.c" && cp "$HERE/harness.c" "$W/$v/" || exit 1
  r=$(cd "$W/$v" && cbmc harness.c -D LEN=${3:-8} --unwind 80 --unwinding-assertions 2>&1 | grep '^VERIFICATION')
  echo "$v: $r"
done
