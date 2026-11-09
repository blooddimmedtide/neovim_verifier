#!/bin/bash
# Verbatim extraction of offset2bytes (spellfile.c) and bytes2offset (spellsuggest.c), sha256-pinned.
set -euo pipefail
NV=${1:?neovim checkout}
here=$(dirname "$0")
awk '/^static int offset2bytes\(int nr, char \*buf_in\)$/{f=1} f{print} f&&/^}$/{exit}' "$NV/src/nvim/spellfile.c" > "$here/offset2bytes.c.inc"
awk '/^static int bytes2offset\(char \*\*pp\)$/{f=1} f{print} f&&/^}$/{exit}' "$NV/src/nvim/spellsuggest.c" > "$here/bytes2offset.c.inc"
(cd "$here" && sha256sum -c pins.sha256)
