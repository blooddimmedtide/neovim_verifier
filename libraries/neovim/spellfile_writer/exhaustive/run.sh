#!/bin/bash
# Usage: bash run.sh <neovim checkout at 7b87ce8>. ~35 s per signedness.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); bash "$here/extract.sh" "$1"
for s in signed unsigned; do
  gcc -O2 -f$s-char -fsanitize=undefined -fno-sanitize-recover -o "$here/chk_$s" "$here/check.c" && "$here/chk_$s"
done
