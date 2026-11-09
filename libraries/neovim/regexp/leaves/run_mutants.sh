#!/bin/bash
# Usage: bash run_mutants.sh <neovim checkout>
# Plants small bugs in the extracted functions and checks that the harness for
# that function rejects each one. Exit 0 = all killed.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d); python3 -I "$HERE/build.py" "$NV" "$W/base.c" || exit 1
status=0; n=0; k=0
while IFS='|' read -r h m; do
  [ -z "$m" ] && continue; n=$((n+1))
  sed "$m" "$W/base.c" > "$W/m.c"
  if cmp -s "$W/base.c" "$W/m.c"; then echo "NOT APPLIED: $m"; status=1; continue; fi
  out=$(cbmc "$HERE/harness.c" --function "$h" -I "$HERE" -DREGEXP_LEAVES_C="\"$W/m.c\"" \
        --arch x86_64 --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
        --undefined-shift-check --conversion-check --unwind 12 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION FAILED"; then k=$((k+1)); echo "killed ($h): $m"; else echo "SURVIVED ($h): $m"; status=1; fi
done <<'MUTANTS'
h_no_Magic|s/#define un_Magic(x)     ((x) + 256)/#define un_Magic(x)     ((x) + 255)/
h_no_Magic|s/#define is_Magic(x)     ((x) < 0)/#define is_Magic(x)     ((x) < -1)/
h_toggle_Magic|/^static int toggle_Magic/,/^}/s/  return Magic(x);/  return x;/
h_toggle_Magic|/^static int toggle_Magic/,/^}/s/    return un_Magic(x);/    return -x;/
h_re_multi_type|s/c == Magic('?')) {/c == Magic('!')) {/
h_re_multi_type|s/c == Magic('{')) {/c == '{') {/
h_re_multi_type|s/    return MULTI_MULT;/    return MULTI_ONE;/
h_re_multi_type|/^static int re_multi_type/,/^}/s/  return NOT_MULTI;/  return c < 0;/
h_backslash_trans|s/    return CAR;/    return '\\n';/
h_backslash_trans|s/  case 'e':/  case 'E':/
h_backslash_trans|/^static int backslash_trans/,/^}/s/  return c;/  return c \& 0x7f;/
h_re_multiline|s/  return prog->regflags \& RF_HASNL;/  return prog->regflags \& 2;/
h_vim_regcomp_had_eol|s/  return had_eol;/  return had_eol != 0;/
h_re_num_cmp|s/((int64_t)(p)\[4\] << 16)/((int64_t)(p)[4] << 8)/
h_re_num_cmp|s/    return val > n;/    return val >= n;/
h_re_num_cmp|s/  if (OPERAND_CMP(scan) == '<') {/  if (OPERAND_CMP(scan) == '>') {/
h_re_num_cmp|s/  uint32_t n = (uint32_t)OPERAND_MIN(scan);/  uint32_t n = (uint32_t)OPERAND_MIN(scan + 1);/
h_nfa_re_num_cmp|s/    return pos > val;/    return pos >= val;/
h_nfa_re_num_cmp|s/  if (op == 2) {/  if (op != 1) {/
h_nfa_re_num_cmp|s/  return val == pos;/  return val <= pos;/
MUTANTS
echo "$k/$n killed"; rm -rf "$W"; exit $status
