#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout at the pinned commit> [mutants]
# simplify_key, unsimplify_key (harness.c) and add_char2buf, special_to_buf (harness_buf.c),
# verbatim code against references, every int input, signed and unsigned char.
# With "mutants": plants bugs and checks that each one fails.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d); status=0
python3 -I "$HERE/../wp/build.py" "$NV" "$W/base.c" || exit 1
python3 -I "$HERE/extract_utf.py" "$NV" "$W/utf.c" || exit 1
cp "$HERE"/harness*.c "$W/"; cp "$W/base.c" "$W/kc.c"
OPTS="--bounds-check --pointer-check --signed-overflow-check --undefined-shift-check --unwind 80 --unwinding-assertions"
one() { (cd "$W" && cbmc "$@" $OPTS 2>&1 | grep -E '^VERIFICATION') ; }
if [ "${2:-}" != mutants ]; then
  for sign in "" --unsigned-char; do
    for t in "harness.c" "harness.c -D UNSIMPLIFY" "harness_buf.c -D ADD_CHAR2BUF" "harness_buf.c"; do
      r=$(one $t $sign); echo "$t ${sign:-signed}: $r"; [ "$r" = "VERIFICATION SUCCESSFUL" ] || status=1
    done
  done
  r=$(cd "$W" && cbmc harness.c -D ALLOW_INT_MIN --signed-overflow-check --unwind 80 2>&1 | grep '^VERIFICATION')
  echo "INT_MIN allowed (finding, expect FAILED): $r"; [ "$r" = "VERIFICATION FAILED" ] || status=1
  exit $status
fi
caught=0; total=0
mut() {  # harness-args old new
  total=$((total+1)); local h=$1 o=$2 n=$3
  python3 -I -c 'import sys; t=open(sys.argv[1]).read(); assert sys.argv[2] in t; open(sys.argv[3],"w").write(t.replace(sys.argv[2],sys.argv[4],1))' "$W/base.c" "$o" "$W/kc.c" "$n" || { echo "mutant $total not applied"; return; }
  r=$(one $h); if [ "$r" = "VERIFICATION FAILED" ]; then caught=$((caught+1)); echo "mutant $total caught"; else echo "MUTANT $total SURVIVED: $n"; fi
}
mut "harness.c" "    *modifiers &= ~MOD_MASK_SHIFT;
    return K_S_TAB;" "    return K_S_TAB;"
mut "harness.c" "        && (*modifiers & modifier_keys_table[i])) {" "        ) {"
mut "harness.c" "      return TERMCAP2KEY(modifier_keys_table[i + 1],
                         modifier_keys_table[i + 2]);" "      return TERMCAP2KEY(modifier_keys_table[i + 2],
                         modifier_keys_table[i + 1]);"
mut "harness.c -D UNSIMPLIFY" "      *modifiers |= modifier_keys_table[i];" "      *modifiers = modifier_keys_table[i];"
mut "harness.c -D UNSIMPLIFY" "  if (!IS_SPECIAL(c)) {" "  if (c < 0) {"  # c > 0 is equivalent (no entry has code 0)
mut "harness_buf.c -D ADD_CHAR2BUF" "      *s++ = KE_FILLER;" "      *s++ = KS_SPECIAL;"
mut "harness_buf.c -D ADD_CHAR2BUF" "  for (int i = 0; i < len; i++) {" "  for (int i = 1; i < len; i++) {"
mut "harness_buf.c" "    dst[dlen++] = (char)(uint8_t)KS_MODIFIER;" "    dst[dlen++] = (char)(uint8_t)KS_EXTRA;"
mut "harness_buf.c" "    dlen = (unsigned)(after - dst);" "    dlen = (unsigned)(after - dst - 1);"
mut "harness_buf.c" "    dlen += (unsigned)utf_char2bytes(key, dst + dlen);" "    dlen = (unsigned)utf_char2bytes(key, dst + dlen);"
echo "caught $caught / $total"; [ $caught = $total ]
