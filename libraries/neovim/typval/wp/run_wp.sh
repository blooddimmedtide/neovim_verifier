#!/bin/bash
# Usage: bash run_wp.sh <neovim checkout> [timeout_seconds] [function...]
# Full-correctness WP proof of the typval functions, no admits. Exit 0 = every goal proved.
# SMOKE=1 adds -wp-smoke-tests: the only expected "Doomed" results are the abort() calls
# after the type switches (dead by design: abort() has precondition \false) and, in
# tv_check_lock, the "false" return of its second value_check_lock call (only made with a set lock).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); T=${2:-30}; shift 2 2>/dev/null || shift $#
FUNCS=${*:-tv_list_len tv_list_uidx tv_list_locked tv_blob_len tv_blob_get tv_check_str_or_nr tv_check_num tv_check_str tv_islocked check_repeat_count tv_get_float tv2bool tv_get_number_chk tv_get_number tv_get_bool_chk tv_get_bool tv_callback_equal value_check_lock tv_check_lock tv_is_func tv_dict_wrong_func_name tv_get_string_buf_chk tv_get_string_buf tv_blob_check_index tv_blob_check_range tv_blob_equal tv_check_for_string_arg tv_check_for_nonempty_string_arg tv_check_for_opt_string_arg tv_check_for_number_arg tv_check_for_opt_number_arg tv_check_for_float_or_nr_arg tv_check_for_bool_arg tv_check_for_opt_bool_arg tv_check_for_blob_arg tv_check_for_list_arg tv_check_for_dict_arg tv_check_for_nonnull_dict_arg tv_check_for_opt_dict_arg tv_check_for_string_or_number_arg tv_check_for_buffer_arg tv_check_for_lnum_arg tv_check_for_string_or_list_arg tv_check_for_string_or_list_or_blob_arg tv_check_for_opt_string_or_list_arg tv_check_for_string_or_func_arg tv_check_for_list_or_blob_arg}
W=$(mktemp -d); status=0
python3 -I "$HERE/build.py" "$NV" "$W/tv.c" || exit 1
if grep -nE '\b(admit|axiom|check)\b' "$W/tv.c"; then echo "forbidden clause"; exit 1; fi
for CH in ""; do  # no function here reads a plain char
for f in $FUNCS; do
  (cd "$W" && frama-c -machdep x86_64 $CH tv.c -wp -wp-fct "$f" -wp-rte -warn-signed-downcast -warn-signed-overflow \
     -wp-model Typed+Cast -wp-prover z3,cvc5 -wp-timeout "$T" -wp-par "$(nproc)" -wp-cache none ${SMOKE:+-wp-smoke-tests} > "wp_$f$CH.log" 2>&1)
  r=$(grep -E "Proved goals" "$W/wp_$f$CH.log" | sed 's/.*goals: *//')
  echo "$f${CH:+ ($CH)}: ${r:-no result}"; grep -E '\[(Timeout|Unknown|Failed)\]|\[kernel\].*(error|Error)|User Error' "$W/wp_$f$CH.log" | head -10 | sed 's/^/   /'
  grep -qE "Proved goals: +([0-9]+) / \1$" "$W/wp_$f$CH.log" || status=1
done; done
echo "logs: $W"; exit $status
