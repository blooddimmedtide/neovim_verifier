#!/bin/bash
# Re-runs every digraph CBMC check. Expected: check_valid OK x2, register FIXED OK x2, register upstream FAILS (finding).
set -u; cd "$(dirname "$0")"
python3 -I extract.py "${NVIM_SRC:-../../../../../verified_neovim}/src/nvim/digraph.c" extracted.c pins.txt >/dev/null || exit 1
python3 -I - <<'PY'
s=open('extracted.c').read(); i=s.index('// ---- check_digraph_chars_valid'); r=s[i:]
open('extracted_register.c','w').write(r)
open('extracted_register_fixed.c','w').write(r.replace('dp->char1 = (uint8_t)char1;','dp->char1 = char1;').replace('dp->char2 = (uint8_t)char2;','dp->char2 = char2;'))
PY
O="--bounds-check --pointer-check --signed-overflow-check --conversion-check --unwinding-assertions"
for s in "" --unsigned-char; do
  cbmc harness.c --function check_valid --unwind 1400 $O $s | tail -1
  cbmc harness_register.c -DFIXED --function check_register --unwind 4 $O $s | tail -1
done
echo "upstream registerdigraph (expected FAILED):"; cbmc harness_register.c --function check_register --unwind 4 $O | tail -1
