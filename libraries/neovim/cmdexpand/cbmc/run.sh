#!/bin/bash
# Re-runs every cmdexpand.c proof (both char signednesses) and the planted-bug checks.
set -u; cd "$(dirname "$0")"; fail=0
C="--bounds-check --pointer-check --signed-overflow-check --unwinding-assertions"
for sc in "" "--unsigned-char"; do
  cbmc harness.c -DN=10 --unwind 12 $C $sc | tail -1 | grep -q SUCCESSFUL || { echo "FAIL global $sc"; fail=1; }
  cbmc harness_sort.c -DN=6 --unwind 8 $C $sc | tail -1 | grep -q SUCCESSFUL || { echo "FAIL sort $sc"; fail=1; }
  cbmc harness_args.c --unwind 14 $C $sc | tail -1 | grep -q SUCCESSFUL || { echo "FAIL args $sc"; fail=1; }
done
# Planted bugs: each must make its proof fail.
t=$(mktemp -d)
mut() { sed "$2" "$1" > "$t/m.c"; sed "s|$1|$t/m.c|" "$3" > "$t/h.c"; cp spec*.h "$t/";
  if cbmc "$t/h.c" $4 2>&1 | tail -1 | grep -q SUCCESSFUL; then echo "MUTANT SURVIVED: $2"; fail=1; else echo "caught: $2"; fi; }
mut fn_global.c 's/arg\[0\] == .\\\\. \&\& arg\[1\] != NUL/0/' harness.c "-DN=6 --unwind 8 --pointer-check"
mut fn_global.c 's/return arg + 1;/return arg;/' harness.c "-DN=6 --unwind 8 --pointer-check"
mut fn_global.c 's/ \&\& arg\[1\] != NUL//' harness.c "-DN=6 --unwind 8 --pointer-check --bounds-check"
mut fn_sort.c 's/return 1;/return -1;/' harness_sort.c "-DN=3 --unwind 5"
mut fn_sort.c 's/return strcmp(p1, p2);/return strcmp(p2, p1);/' harness_sort.c "-DN=3 --unwind 5"
mut fn_args.c 's/"clear"/"clea"/' harness_args.c "--unwind 14"
mut fn_args.c 's/idx == 0/idx <= 0/' harness_args.c "--unwind 14"
exit $fail
