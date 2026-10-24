#!/bin/bash
# Usage: mutants.sh <neovim-src-dir>
# Sanity check that the CBMC harnesses are not vacuous: plant known bugs in a
# copy of base64.c and confirm at least one harness fails for each.
# Exit 0 = every mutant was caught.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
NV=$1; TMP=$(mktemp -d); missed=0
mutants=(
  's/src_i + 7 < src_len/src_i + 6 < src_len/::fast path reads past end'
  's/(bits_be >> 16) \& 0x3F/(bits_be >> 17) \& 0x3F/::wrong shift in fast path'
  's/if (acc_len > 4 ||/if (acc_len > 6 ||/::decoder accepts leftover bits'
  's/padding_chars != padding_len/padding_chars < padding_len/::decoder accepts extra padding'
  "s/\['+'\] = 63/['-'] = 63/::wrong alphabet"
  's/(acc << 6) \& 0xFFF/(acc << 6) \& 0x7FF/::wrong accumulator mask'
)
for m in "${mutants[@]}"; do
  sedexpr=${m%% ::*}; sedexpr=${m%%::*}; name=${m#*::}
  mkdir -p "$TMP/src/nvim"; cp "$NV/src/nvim/base64.c" "$TMP/src/nvim/"
  sed -i "$sedexpr" "$TMP/src/nvim/base64.c"
  if cmp -s "$NV/src/nvim/base64.c" "$TMP/src/nvim/base64.c"; then
    echo "STALE  $name (pattern no longer matches upstream)"; missed=1; continue
  fi
  caught=no
  for t in "encode 7" "encode 9" "encode 11" "decode 8" "roundtrip 8"; do
    if ! bash "$HERE/run_cbmc.sh" "$TMP" $t >/dev/null 2>&1; then caught="yes ($t)"; break; fi
  done
  echo "$caught  $name"; [ "$caught" = no ] && missed=1
done
rm -rf "$TMP"; exit $missed
