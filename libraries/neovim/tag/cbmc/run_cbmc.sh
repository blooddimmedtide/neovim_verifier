#!/bin/bash
# Usage: run_cbmc.sh <neovim checkout>   (pinned commit 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd)
set -euo pipefail
cd "$(dirname "$0")"
python3 -I build.py "$1" tag_extract.c
N=${N:-8}; U=$((N + 3))
for sign in "" "--unsigned-char"; do
  for h in h_parse_tag_line h_tag_strnicmp h_test_for_static h_matching_line_len; do
    echo "== $h ${sign:-signed-char} N=$N"
    cbmc harness.c -DN=$N --function $h $sign --arch x86_64 --bounds-check --pointer-check \
      --signed-overflow-check --unsigned-overflow-check --pointer-overflow-check \
      --undefined-shift-check --unwind $U --unwinding-assertions \
--object-bits 12 2>&1 | tail -1
  done
done
