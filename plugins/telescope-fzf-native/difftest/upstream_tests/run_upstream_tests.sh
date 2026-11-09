#!/bin/bash
# Usage: bash run_upstream_tests.sh <path/to/fzf.c> <path/to/plugin/test/test.c>
# 1. the plugin's own C tests (test/test.c, 63 tests) against the given fzf.c,
#    with ASan/UBSan;  2. the same tests with the five algorithms that have a
#    full reference replaced by that reference (spec.h): the spec must give the
#    upstream expected values. The v2 tests use the real v2 in both runs.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
F=$(cd "$(dirname "$1")" && pwd)/$(basename "$1"); T=$2; W=$(mktemp -d)
SAN="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=all -Wno-discarded-qualifiers -Wno-incompatible-pointer-types -fno-sanitize=nonnull-attribute"  # test.c:689 memcmp(NULL, .., 0) is in the test, not fzf.c
gcc $SAN -I "$HERE" -I "$(dirname "$F")" -include stdint.h "$T" "$F" -o "$W/t_code" || exit 1
echo "== upstream tests against $(basename "$F")"; "$W/t_code"; a=$?
REDIR="-Dfzf_fuzzy_match_v1=ref_fuzzy_match_v1 -Dfzf_exact_match_naive=ref_exact_match_naive -Dfzf_prefix_match=ref_prefix_match -Dfzf_suffix_match=ref_suffix_match -Dfzf_equal_match=ref_equal_match"
gcc $SAN -I "$HERE" -I "$(dirname "$F")" -include stdint.h $REDIR -c "$T" -o "$W/test.o" || exit 1
gcc $SAN -I "$HERE/../../cbmc" -I "$(dirname "$F")" -c "$HERE/ref_algos.c" -o "$W/ref.o" || exit 1
gcc $SAN -I "$(dirname "$F")" "$W/test.o" "$W/ref.o" "$F" -o "$W/t_ref" || exit 1
echo "== upstream tests with the reference in place of v1/exact/prefix/suffix/equal (PatternParsing skipped: it compares the function pointers)"; EXAM_SKIP=PatternParsing "$W/t_ref"; b=$?
rm -rf "$W"; [ $a -eq 0 ] && [ $b -eq 0 ]
