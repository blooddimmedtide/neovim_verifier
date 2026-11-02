#!/bin/bash
# Build a libFuzzer harness against a sanitizer + coverage build of Neovim.
# Usage: build.sh <nvim build dir> <harness.c> <out>
set -e
B=$1; H=$2; OUT=$3
HERE=$(cd "$(dirname "$0")" && pwd)
NJ=$B/build.ninja
get() { grep -A8 "^build src/nvim/CMakeFiles/nvim_bin.dir/regexp.c.o" "$NJ" | grep "^  $1 = " | sed "s/^  $1 = //"; }
DEFINES=$(get DEFINES); FLAGS=$(get FLAGS); INCLUDES=$(get INCLUDES)
LIBS=$(grep -A6 "^build bin/nvim:" "$NJ" | grep "^  LINK_LIBRARIES = " | sed 's/^  LINK_LIBRARIES = //')
SRC=$(grep -m1 "^CMAKE_HOME_DIRECTORY\|^# CMAKE_HOME" "$B/CMakeCache.txt" | sed 's/.*=//')
OBJS=$(find "$B/src/nvim/CMakeFiles/nvim_bin.dir" -name '*.o' ! -path '*/nvim_bin.dir/main.c.o')
W="-Wno-missing-prototypes -Wno-conversion -Wno-shadow -Wno-strict-prototypes -Wno-pedantic"
clang $DEFINES $INCLUDES $FLAGS $W -c "$HERE/main_shim.c" -o "$OUT.shim.o"
clang $DEFINES $INCLUDES $FLAGS $W -c "$H" -o "$OUT.o"
clang -flto=thin -fsanitize=fuzzer,address,undefined -rdynamic "$OUT.o" "$OUT.shim.o" $OBJS $LIBS -o "$OUT"
