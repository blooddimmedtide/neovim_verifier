#!/bin/bash
# Usage: bash run_mutants.sh <fixed neovim checkout>
# Plants small bugs in the extracted set_last_csearch / utf_is_trail_byte and checks
# that the CBMC harness rejects every one. Exit 0 = all killed.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d); python3 -I "$HERE/build.py" "$NV" "$W/base.c" | grep -qx fixed || { echo "not the fixed version"; exit 1; }
status=0; n=0; k=0
while IFS= read -r m; do
  [ -z "$m" ] && continue; n=$((n+1))
  sed "$m" "$W/base.c" > "$W/m.c"
  if cmp -s "$W/base.c" "$W/m.c"; then echo "NOT APPLIED: $m"; status=1; continue; fi
  out=$(cbmc "$HERE/harness.c" --function h_set_last_csearch -I "$HERE" -DSEARCH_C="\"$W/m.c\"" -DMAXLEN=64 \
        --arch x86_64 --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
        --unwind 35 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION FAILED"; then k=$((k+1)); echo "killed: $m"; else echo "SURVIVED: $m"; status=1; fi
done <<'MUTANTS'
s/len = MAX_SCHAR_SIZE;/len = MAX_SCHAR_SIZE + 1;/
s/len > MAX_SCHAR_SIZE) {/len > MAX_SCHAR_SIZE + 1) {/
s/while (len > 0 \&\&/while (len > 1 \&\&/
s/utf_is_trail_byte((uint8_t)s\[len\])/utf_is_trail_byte((uint8_t)s[len - 1])/
s/  CLEAR_FIELD(lastc_bytes);/  ;/
s/  lastc_bytelen = len;/  lastc_bytelen = len - (len > 0);/
s/memcpy(lastc_bytes, s, (size_t)len);/memcpy(lastc_bytes, s, (size_t)len - 1);/
s/return (uint8_t)(byte \& 0xC0U) == 0x80U;/return (uint8_t)(byte \& 0x80U) == 0x80U;/
s/\*lastc = (uint8_t)c;/lastc[1] = (uint8_t)c;/
MUTANTS
echo "$k/$n killed"; rm -rf "$W"; exit $status
