#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> [math_c.c instead of building one]
# Proves src/nvim/math.c with CBMC for every input, both for the GCC/Clang
# build (builtins) and the portable fallback loops. Exit 0 = all proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d); status=0
for v in builtin fallback; do
  if [ $# -ge 2 ]; then cp "$2" "$W/m.c"; [ $v = fallback ] && sed -i '0,/^#define FUNC_ATTR_CONST$/s//#define FUNC_ATTR_CONST\n#undef __GNUC__\n#undef __clang__/' "$W/m.c"
  else python3 -I "$HERE/build.py" "$NV" "$W/m.c" $([ $v = fallback ] && echo --fallback) || exit 1; fi
  for h in h_classify h_ctz h_popcount h_append_digit h_trim; do
    out=$(cbmc "$HERE/harness.c" --function $h -DMATH_C="\"$W/m.c\"" --arch x86_64 --bounds-check \
          --pointer-check --signed-overflow-check --undefined-shift-check --unwind 70 --unwinding-assertions 2>&1)
    if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h ($v): proved"
    else echo "$h ($v): FAILED"; echo "$out" | grep FAILURE | head -5; status=1; fi
  done
done
rm -rf "$W"; exit $status
