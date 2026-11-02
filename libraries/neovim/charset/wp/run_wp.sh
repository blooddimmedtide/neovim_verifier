#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> [timeout_seconds] [--fixed] [function ...]
# --fixed: the checkout is the fixed fork (vim_str2nr's fix; its upstream-only precondition dropped)
# Full-correctness proof of charset.c string helpers (and the ascii_defs.h helpers
# they call) with Frama-C WP, no admits. build.py makes an annotated copy of the exact
# upstream text (sha256 pinned; stripping the ACSL comments gives the upstream text
# back); each function is proved in its own run. Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-60}; shift; shift
FIX=""; if [ "${1:-}" = "--fixed" ]; then FIX=--fixed; shift; fi
W=$(mktemp -d); cp -r "$HERE/stubs" "$W/"; status=0
python3 -I "$HERE/lemmas.py" || status=1
python3 -I "$HERE/build.py" "$NV" "$W/cs.c" $FIX || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/cs.c" "$W"/stubs/*.h "$W"/stubs/nvim/*.h; then echo "forbidden clause"; exit 1; fi
run() {  # $1 = label, rest = frama-c selection options
  local l=$1; shift
  (cd "$W" && frama-c -machdep x86_64 -cpp-extra-args="-I stubs" cs.c -wp "$@" -wp-rte \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none > "wp_$l.log" 2>&1)
  local r; r=$(grep -E "Proved goals" "$W/wp_$l.log" | sed 's/.*goals: *//')
  echo "$l: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|\[kernel\].*(error|Error)|User Error' "$W/wp_$l.log" | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$l.log" || status=1
}
FUNCS="${*:-ascii_iswhite ascii_isdigit ascii_isxdigit ascii_isbdigit ascii_isodigit nr2hex skipwhite skipwhite_len getwhitecols
  skipdigits skipbin skiphex skiptodigit skiptobin skiptohex skiptowhite skiptowhite_esc skip_to_newline
  vim_isblankline hex2nr hexhex2nr rem_backslash backslash_halve backslash_halve_save vim_str2nr subj_exists try_getdigits getdigits getdigits_int getdigits_long getdigits_int32}"
for f in $FUNCS; do run "$f" -wp-fct "$f"; done
echo "logs: $W"; exit $status
