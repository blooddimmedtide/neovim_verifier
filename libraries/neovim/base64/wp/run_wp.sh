#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> [timeout_seconds]
# Full-correctness proof of src/nvim/base64.c with Frama-C WP, no admits.
#   1. checks the bit lemmas with Z3 bit-vectors (lemmas.py)
#   2. proves each tool patch equal to the original statement (CBMC, all inputs)
#   3. annotates a pristine copy and proves each function in its own WP run
#   4. fails if the annotated file contains admit, axiom or assumes
# Works on upstream and on the fixed decoder (annotate.py detects which).
# Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-300}
W=$(mktemp -d); cp -r "$HERE/stubs" "$W/"; status=0
python3 -I "$HERE/lemmas.py" || status=1
bash "$HERE/../equiv/run_equiv.sh" "$NV" || status=1
for part in enc dec; do
  fn=$([ $part = enc ] && echo base64_encode || echo base64_decode)
  python3 -I "$HERE/annotate.py" "$NV/src/nvim/base64.c" "$W/b64_$part.c" $part || exit 1
  if grep -nE '\b(admit|axiom|assumes|check)\b' "$W/b64_$part.c" "$W"/stubs/*.h "$W"/stubs/*/*.h; then echo "forbidden clause"; status=1; fi
  (cd "$W" && frama-c -cpp-extra-args="-I stubs" -machdep x86_64 "b64_$part.c" \
     -wp -wp-fct "$fn" -wp-rte -wp-model Typed+Cast -wp-prover z3,cvc5 \
     -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none > "wp_$part.log" 2>&1)
  grep -E "Proved goals|Timeout\]|Unknown\]|Failed\]" "$W/wp_$part.log"
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$part.log" || status=1
done
echo "logs: $W"; exit $status
