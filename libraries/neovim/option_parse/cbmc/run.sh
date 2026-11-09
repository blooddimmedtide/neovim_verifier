#!/bin/sh
# usage: run.sh [N]   (N = largest buffer size, default 16; loops unwound to N+2)
set -e
N=${1:-16}
for f in "" --unsigned-char; do
  cbmc harness.c -DN=$N $f --bounds-check --pointer-check --signed-overflow-check \
    --unsigned-overflow-check --pointer-overflow-check --unwind $((N+2)) --unwinding-assertions
done
