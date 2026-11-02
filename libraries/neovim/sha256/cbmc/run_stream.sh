#!/bin/bash
# Usage: bash run_stream.sh <neovim checkout or fork> [fixed]
# Stream proofs of sha256_update (loop contract, every length) with CBMC/DFCC.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d); status=0
python3 -I "$HERE/build.py" "$NV" "$W/sha256_x.c" || exit 1
D="${EXTRA:-}"; [ "${2:-}" = fixed ] && D="$D -DSHA256_FIXED"
for h in ${HARNESSES:-h_update}; do
  goto-cc "$HERE/harness_stream.c" -o "$W/a.goto" --function "$h" -I "$HERE/stubs" -I "$NV/src" $D \
     -DSHA256_X_C="\"$W/sha256_x.c\"" || { status=1; continue; }
  goto-instrument --replace-calls sha256_process:rec_process "$W/a.goto" "$W/b.goto" >/dev/null || { status=1; continue; }
  goto-instrument --dfcc "$h" --apply-loop-contracts "$W/b.goto" "$W/c.goto" > "$W/instr_$h.log" 2>&1 || { cat "$W/instr_$h.log" | tail -5; status=1; continue; }
  out=$(cbmc "$W/c.goto" --no-malloc-may-fail --bounds-check --pointer-check --signed-overflow-check \
        --undefined-shift-check --unwind 3 --unwinding-assertions 2>&1)
  if echo "$out" | grep -q "VERIFICATION SUCCESSFUL"; then echo "$h: proved"
  else echo "$h: FAILED"; echo "$out" | grep -E 'FAILURE|ERROR|error' | head -8; status=1; fi
done
echo "work: $W"; exit $status
