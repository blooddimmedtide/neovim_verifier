#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout>
# Full-correctness proofs of 8 small regexp.c functions with CBMC (x86_64, both
# char signednesses). Exit 0 = every harness proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d)
python3 -I "$HERE/build.py" "$NV" "$W/leaves.c" || exit 1
if grep -n '__CPROVER_assume' "$W/leaves.c"; then echo "assume in code under test"; exit 1; fi
status=0
for sign in signed --unsigned-char; do
  for h in ${ONLY:-h_no_Magic h_toggle_Magic h_re_multi_type h_backslash_trans h_re_multiline h_vim_regcomp_had_eol h_re_num_cmp h_nfa_re_num_cmp}; do
    out=$(cbmc "$HERE/harness.c" --function "$h" -I "$HERE" -DREGEXP_LEAVES_C="\"$W/leaves.c\"" \
          --arch x86_64 ${sign#signed} --no-malloc-may-fail --bounds-check --pointer-check \
          --signed-overflow-check --undefined-shift-check --conversion-check --unwind 12 --unwinding-assertions 2>&1)
    if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "${h#h_} ($sign): proved"
    else echo "${h#h_} ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|error' | head -5; status=1; fi
  done
done
rm -rf "$W"; exit $status
