#!/bin/bash
# Usage: run_all.sh <neovim-src-dir> [max_encode_len] [max_decode_len] [max_roundtrip_len]
# Runs every harness for every exact length up to the bounds, 4 at a time.
# Writes $OUT/<harness>-<len>.log and $OUT/summary.tsv (OUT defaults to ./cbmc-results).
# Exit 0 = all proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
NV=$1; E=${2:-24}; D=${3:-16}; R=${4:-12}
OUT=$(mkdir -p "${OUT:-$PWD/cbmc-results}" && cd "${OUT:-$PWD/cbmc-results}" && pwd); rm -f "$OUT/"*.log "$OUT/summary.tsv"
jobs=()
for l in $(seq 0 $E); do jobs+=("encode $l"); done
for l in $(seq 0 $D); do jobs+=("decode $l"); done
for l in $(seq 0 $R); do jobs+=("roundtrip $l"); done
printf '%s\n' "${jobs[@]}" | xargs -P "$(nproc)" -L 1 bash -c '
  start=$(date +%s)
  bash "'"$HERE"'/run_cbmc.sh" "'"$NV"'" "$0" "$1" > "'"$OUT"'/$0-$1.log" 2>&1
  rc=$?; end=$(date +%s)
  status=$([ $rc -eq 0 ] && echo PROVED || echo FAILED)
  printf "%s\t%s\t%s\t%ss\n" "$0" "$1" "$status" "$((end-start))" >> "'"$OUT"'/summary.tsv"
'
sort -k1,1 -k2,2n "$OUT/summary.tsv" -o "$OUT/summary.tsv"
cat "$OUT/summary.tsv"
! grep -q FAILED "$OUT/summary.tsv"
