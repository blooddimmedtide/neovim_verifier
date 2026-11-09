#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout at the pinned commit> [timeout] [function...]
# Exit 0 = every goal of every listed function proved (no admits, no axioms).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-30}; shift 2 2>/dev/null || shift $#
FUNCS=${*:-lemmas mf_free_fnames mf_set_fnames mf_new_page_size mf_alloc_bhdr mf_free_bhdr mf_ins_free mf_rem_free mf_need_trans ml_new_data ml_new_ptr ml_add_stack ml_flush_deleted_bytes ml_line_alloced ml_add_deleted_len_buf ml_add_deleted_len ml_get ml_get_buf ml_get_buf_mut ml_get_pos ml_get_pos_len ml_timestamp ml_append ml_replace ml_replace_len ml_delete}
W=$(mktemp -d); status=0
python3 -I "$HERE/build.py" "$NV" "$W/ml.c" || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/ml.c"; then echo "forbidden clause"; exit 1; fi
for f in $FUNCS; do
  if [ "$f" = lemmas ]; then sel="-wp-prop=@lemma"; else sel="-wp-fct $f"; fi
  (cd "$W" && frama-c -machdep x86_64 -cpp-extra-args="-I $HERE/../../memory/wp/stubs" ml.c -wp $sel -wp-rte -warn-signed-downcast -warn-unsigned-overflow \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none -wp-smoke-tests > "wp_$f.log" 2>&1)
  r=$(grep -E "Proved goals" "$W/wp_$f.log" | sed 's/.*goals: *//')
  echo "$f: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|[Ee]rror|Doomed' "$W/wp_$f.log" | head -10 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$f.log" || status=1
done
echo "logs: $W"; exit $status
