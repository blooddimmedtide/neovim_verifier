#!/bin/bash
# Usage: bash run_difftest.sh <neovim checkout>
# Compiles the exact functions with gcc -O2 (signed and unsigned char) and compares them
# with the reference. getdecchrs is included only for the fixed fork (upstream overflows
# on long runs; see findings/regexp-getdecchrs-overflow.md). Exit 0 = no mismatch.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d); status=0
python3 -I "$HERE/../cbmc/build.py" "$NV" "$W/num.c" || exit 1
dec=""
if python3 -I "$HERE/../wp/build.py" "$NV" "$W/dec.c" | grep -q "getdecchrs/fixed"; then
  sed -n '/^\/\/ src\/nvim\/regexp.c:.*getdecchrs\|^static int64_t getdecchrs/,$p' "$W/dec.c" \
    | sed 's| /\*@ ghost ([^)]*) \*/||' | perl -0pe 's|/\*@.*?\*/\n||gs' > "$W/dec_only.c"
  { echo "static int curchr;"; echo "#include <limits.h>"; cat "$W/dec_only.c"; } >> "$W/num.c"
  dec="-DHAVE_DEC"
fi
for sign in -fsigned-char -funsigned-char; do
  gcc -O2 $sign $dec -I "$HERE" -DREGEXP_NUM_C="\"$W/num.c\"" "$HERE/difftest.c" -o "$W/dt" || exit 1
  echo -n "$sign: "; "$W/dt" > "$W/out"; rc=$?; tail -1 "$W/out"; [ $rc -eq 0 ] || status=1
done
rm -rf "$W"; exit $status
