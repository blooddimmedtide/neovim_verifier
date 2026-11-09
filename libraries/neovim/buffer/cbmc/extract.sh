#!/bin/bash
# Verbatim extraction from src/nvim/buffer.c (pinned commit 7b87ce8); sha256 pinned per piece.
# Usage: bash extract.sh <path to buffer.c> <outdir>
set -eu
src=$1; out=$2; mkdir -p "$out"
sed -n '159,165p' "$src" > "$out/calc_percentage.c"
sed -n '2528,2537p' "$src" > "$out/buf_time_compare.c"
cd "$out"
sha256sum -c --quiet <<SUM
57152294184efe1f224e84c9986a82a64b7fd76878fd8527debad1f6f3487a43  calc_percentage.c
763e96ccfbe61bfb6eb5bf15e60bc788578b034e92ad72b9015267547bb0e92a  buf_time_compare.c
SUM
