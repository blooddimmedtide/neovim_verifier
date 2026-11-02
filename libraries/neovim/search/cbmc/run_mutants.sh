#!/bin/bash
# Usage: bash run_mutants.sh <fixed neovim checkout>
# Plants small bugs in the extracted search.c functions and checks that the
# CBMC harness for that function rejects every one. Exit 0 = all killed.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d); python3 -I "$HERE/build.py" "$NV" "$W/base.c" | grep -qx fixed || { echo "not the fixed version"; exit 1; }
status=0; n=0; k=0
while IFS='|' read -r file h m; do
  [ -z "$m" ] && continue; n=$((n+1))
  sed "$m" "$W/base.c" > "$W/m.c"
  if cmp -s "$W/base.c" "$W/m.c"; then echo "NOT APPLIED: $m"; status=1; continue; fi
  out=$(cbmc "$HERE/$file" --function "$h" -I "$HERE" -DSEARCH_C="\"$W/m.c\"" -DMAXLEN=64 \
        --arch x86_64 --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
        --unwind 35 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION FAILED"; then k=$((k+1)); echo "killed ($h): $m"; else echo "SURVIVED ($h): $m"; status=1; fi
done <<'MUTANTS'
harness.c|h_set_last_csearch|s/len = MAX_SCHAR_SIZE;/len = MAX_SCHAR_SIZE + 1;/
harness.c|h_set_last_csearch|s/len > MAX_SCHAR_SIZE) {/len > MAX_SCHAR_SIZE + 1) {/
harness.c|h_set_last_csearch|s/while (len > 0 \&\&/while (len > 1 \&\&/
harness.c|h_set_last_csearch|s/utf_is_trail_byte((uint8_t)s\[len\])/utf_is_trail_byte((uint8_t)s[len - 1])/
harness.c|h_set_last_csearch|s/  CLEAR_FIELD(lastc_bytes);/  ;/
harness.c|h_set_last_csearch|s/  lastc_bytelen = len;/  lastc_bytelen = len - (len > 0);/
harness.c|h_set_last_csearch|s/memcpy(lastc_bytes, s, (size_t)len);/memcpy(lastc_bytes, s, (size_t)len - 1);/
harness.c|h_set_last_csearch|s/return (uint8_t)(byte \& 0xC0U) == 0x80U;/return (uint8_t)(byte \& 0x80U) == 0x80U;/
harness.c|h_set_last_csearch|s/\*lastc = (uint8_t)c;/lastc[1] = (uint8_t)c;/
accessors.c|h_get_search_pat|s/  return mr_pattern;/  return spats[0].pat;/
accessors.c|h_last_search_pattern|s/  return spats\[RE_SEARCH\].pat;/  return spats[RE_SUBST].pat;/
accessors.c|h_last_search_pattern_len|s/  return spats\[RE_SEARCH\].patlen;/  return spats[RE_SEARCH].patlen + 1;/
accessors.c|h_last_csearch|s/  return lastc_bytes;/  return lastc_bytes + 1;/
accessors.c|h_last_csearch_forward|s/  return lastcdir == FORWARD;/  return lastcdir != BACKWARD;/
accessors.c|h_last_csearch_until|s/  return last_t_cmd;/  return !last_t_cmd;/
accessors.c|h_set_csearch_direction|s/  lastcdir = cdir;/  lastcdir = cdir == BACKWARD ? BACKWARD : FORWARD;/
accessors.c|h_set_csearch_until|s/  last_t_cmd = t_cmd;/  last_t_cmd = t_cmd == 1;/
accessors.c|h_set_search_direction|s/  spats\[0\].off.dir = (char)cdir;/  spats[1].off.dir = (char)cdir;/
accessors.c|h_first_submatch|s/    if (submatch == 9) {/    if (submatch == 8) {/
accessors.c|h_first_submatch|s/      submatch = 0;/      submatch = 9;/
accessors.c|h_first_submatch|s/    if (rp->startpos\[submatch\].lnum >= 0) {/    if (rp->startpos[submatch].lnum > 0) {/
accessors.c|h_first_submatch|s/  for (submatch = 1;; submatch++) {/  for (submatch = 0;; submatch++) {/
accessors.c|h_search_pattern_cleared|s/substitute ? RE_SUBST : RE_SEARCH/substitute ? RE_SEARCH : RE_SUBST/
accessors.c|h_set_last_used_pattern|s/is_substitute_pattern ? 1 : 0/is_substitute_pattern ? 2 : 0/
accessors.c|h_search_was_last_used|s/  return last_idx == 0;/  return last_idx != 1;/
MUTANTS
echo "$k/$n killed"; rm -rf "$W"; exit $status
