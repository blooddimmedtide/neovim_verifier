#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>
# Full-correctness proofs with CBMC (x86_64, both char signednesses):
# set_last_csearch (harness.c): on the fixed fork the proof must succeed; on
# upstream it must fail with an out-of-bounds write and the stale-bytes
# violation (the finding). The 21 accessors (accessors.c): proved on both.
# Exit 0 = every outcome as expected for the version found.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d)
ver=$(python3 -I "$HERE/build.py" "$NV" "$W/search_cs.c") || exit 1
if grep -n '__CPROVER_assume' "$W/search_cs.c"; then echo "assume in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
  # MAXLEN 64 covers every path: the function touches at most s[0..32].
  # The second run lets len be any non-negative int.
  for maxlen in 64 2147483647; do
    out=$(cbmc "$HERE/harness.c" --function h_set_last_csearch -I "$HERE" \
          -DSEARCH_C="\"$W/search_cs.c\"" -DMAXLEN=$maxlen \
          --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
          --signed-overflow-check --undefined-shift-check --unwind 35 --unwinding-assertions 2>&1)
    if [ "$ver" = fixed ]; then
      if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "set_last_csearch fixed ($sign, len<=$maxlen): proved"
      else echo "set_last_csearch fixed ($sign, len<=$maxlen): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -5; status=1; fi
    else
      if echo "$out" | grep -q "VERIFICATION FAILED" && echo "$out" | grep -q "tail cleared.*FAILURE" \
         && echo "$out" | grep -qE "memcpy.*FAILURE|dereference failure.*FAILURE|pointer outside.*FAILURE"; then
        echo "set_last_csearch upstream ($sign, len<=$maxlen): refuted as expected (overflow + stale bytes)"
      else echo "set_last_csearch upstream ($sign, len<=$maxlen): unexpected result"; echo "$out" | grep -E 'FAILURE|error|VERIFICATION' | head -8; status=1; fi
    fi
  done
done
ACC="h_get_search_pat h_last_search_pattern h_last_search_pattern_len h_last_csearch h_last_csearch_forward
     h_last_csearch_until h_set_csearch_direction h_set_csearch_until h_set_search_direction h_first_submatch
     h_search_pattern_cleared h_set_last_used_pattern h_search_was_last_used
     h_free_spat h_set_vv_searchforward h_last_search_pat h_get_search_pattern h_get_substitute_pattern
     h_get_search_pattern_timestamp h_set_search_pattern h_set_substitute_pattern"
for sign in signed --unsigned-char; do
  for h in $ACC; do
    out=$(cbmc "$HERE/accessors.c" --function "$h" -I "$HERE" -DSEARCH_C="\"$W/search_cs.c\"" \
          --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
          --signed-overflow-check --undefined-shift-check --unwind 35 --unwinding-assertions 2>&1)
    if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "${h#h_} ($sign): proved"
    else echo "${h#h_} ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -5; status=1; fi
  done
done
rm -rf "$W"; exit $status
