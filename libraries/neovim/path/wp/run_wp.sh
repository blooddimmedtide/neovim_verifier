#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> <upstream|fixed> [timeout_seconds] [function...]
# Proof of path.c functions with Frama-C WP, no admits; each function in its own run,
# with both char signednesses. Exit 0 = every goal proved.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); MODE=$2; T=${3:-30}; shift 3 2>/dev/null || shift $#
FUNCS=${*:-ascii_isdigit vim_ispathsep vim_ispathsep_nocolon vim_ispathlistsep path_head_length is_path_head path_skip_sep get_past_head path_tail path_next_component path_is_absolute path_has_drive_letter path_is_url path_with_url vim_isAbsName after_pathsep path_tail_with_sep invocation_path_tail}
W=$(mktemp -d); mkdir -p "$W/stubs"; cp "$HERE"/stubs/*.h "$HERE/../../memory/wp/stubs/vp_string.h" "$W/stubs/"; status=0
gcc -std=c11 -Wall -Werror "$HERE/../equiv/literals.c" -o "$W/literals" && "$W/literals" || exit 1
python3 -I "$HERE/build.py" "$NV" "$W/path.c" "$MODE" || exit 1
# no admit/axiom/check clause in any ACSL annotation (C comments may say "check")
if cat "$W/path.c" "$W"/stubs/*.h | python3 -I -c 'import re,sys; t=sys.stdin.read(); sys.exit(any(re.search(r"\b(admit|axiom|check)\b", a) for a in re.findall(r"/\*@.*?\*/", t, re.S)))'; then :; else echo "forbidden clause"; exit 1; fi
for md in x86_64 "$HERE/machdep_x86_64_uchar.yaml"; do
for f in $FUNCS; do
  l="$f$([ $md = x86_64 ] || echo -uchar)"
  (cd "$W" && frama-c -machdep "$md" -cpp-extra-args="-I stubs" path.c -wp -wp-fct "$f" -wp-rte -warn-signed-downcast \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -no-cpp-frama-c-compliant -wp-cache none > "wp_$l.log" 2>&1)
  r=$(grep -E "Proved goals" "$W/wp_$l.log" | sed 's/.*goals: *//')
  echo "$MODE $l: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|error|Error' "$W/wp_$l.log" | head -8 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$l.log" || status=1
done; done
echo "logs: $W"; exit $status
