#!/bin/bash
# Usage: bash gen.sh <neovim checkout> <out dir> — runs Neovim's own gen_keycodes.lua
# (LuaJIT, with vimshim.lua providing the 6 vim.* helpers it uses) to make key_names_table.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); mkdir -p "$2"; OUT=$(cd "$2" && pwd)
(cd "$NV" && LUA_PATH="src/?.lua;;" luajit -e "dofile('$HERE/vimshim.lua')" src/gen/gen_keycodes.lua \
   "$OUT/keycode_names.generated.h" src/nvim/keycodes.lua)
echo "4adc8b52c090cb462f83dfc2a676c0946d1bc5277eeb6a0c463ea2bd5f703c57  $OUT/keycode_names.generated.h" | sha256sum -c --quiet
