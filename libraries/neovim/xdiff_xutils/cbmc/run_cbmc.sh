#!/bin/bash
# Usage: bash run_cbmc.sh <neovim checkout> [xutils.c to use instead]
# CBMC proofs of the loop-free (or bounded-loop) functions of src/xdiff/xutils.c.
# ONLY=<regex> limits the run to matching harness names. FULL=1 also proves the hunk header
# text for every long (fixed code only: upstream prints negative numbers wrong).
# Exit 0 = every harness proved, with all loop bounds proved enough.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd)
W=$(mktemp -d); mkdir -p "$W/xdiff" "$W/nvim"
for f in xinclude.h xmacros.h xdiff.h xtypes.h xutils.h xprepare.h xdiffi.h xemit.h; do cp "$NV/src/xdiff/$f" "$W/xdiff/"; done
cp "${2:-$NV/src/xdiff/xutils.c}" "$W/xdiff/xutils.c"; cp "$HERE/memory.h" "$W/nvim/memory.h"
UP_C=9972da1b2e6cd1017590597d08052906ea2fd812430008d1eea6242a1a56cd0b     # 7b87ce8
FIX_C=03680d3e6d9beb279741f33b9d1f8c3d3c9b5d37cf655e59e4d23e6d750eb059    # fork: the three xdiff fixes merged
H=eb495aad474092cbc35ac49bb01c4f9742a3ddc15cc26b4b9f2bce2a4765f725   # the 8 headers, concatenated
[ "$(cd "$W/xdiff" && cat xinclude.h xmacros.h xdiff.h xtypes.h xutils.h xprepare.h xdiffi.h xemit.h | sha256sum | cut -d' ' -f1)" = "$H" ] || { echo "xdiff headers changed upstream"; exit 1; }
c=$(sha256sum < "$W/xdiff/xutils.c" | cut -d' ' -f1)
if [ $# -lt 2 ] && [ "$c" != "$UP_C" ] && [ "$c" != "$FIX_C" ]; then echo "xutils.c changed upstream: $c"; exit 1; fi
if grep -n '__CPROVER' "$W/xdiff/"*; then echo "CPROVER in code under test"; exit 1; fi
status=0
list="h_bogosqrt:34 h_hashbits:34 h_num_out:22 h_emit_diffrec:31 h_cha_alloc:2 h_mmfile:2 h_emit_hunk_hdr_cb:2 h_emit_hunk_hdr_text:22 h_fall_back_diff:2"
[ -n "${FULL:-}" ] && list="$list h_emit_hunk_hdr_text:22:-DFULL_RANGE"
for sign in signed --unsigned-char; do
for hu in $list; do
  h=${hu%%:*}; rest=${hu#*:}; u=${rest%%:*}; d=""; [ "$rest" != "$u" ] && d=${rest#*:}
  if [ -n "${ONLY:-}" ] && ! [[ $h =~ $ONLY ]]; then continue; fi
  out=$(cbmc "$HERE/harness.c" --function "$h" -I "$W/xdiff" -DXUTILS_C="\"$W/xdiff/xutils.c\"" $d \
        --arch x86_64 ${sign#signed} --bounds-check --pointer-check --signed-overflow-check --conversion-check \
        --unwind "$u" --unwinding-assertions --sat-solver cadical 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h$d ($sign): proved"
  else echo "$h$d ($sign): FAILED"; echo "$out" | grep -E 'FAILURE|rror' | head -8; status=1; fi
done
done
rm -rf "$W"; exit $status
