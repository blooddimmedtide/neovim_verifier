#!/bin/bash
# Planted bugs: each edits one line of the built file; WP must then fail that function.
# Usage: bash mutants.sh <neovim checkout>. Exit 0 = every mutant caught.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); W=$(mktemp -d); bad=0
python3 -I "$HERE/build.py" "$NV" "$W/base.c" || exit 1
M=(
 "ml_new_data|dp->db_free = dp->db_txt_start - (unsigned)HEADER_SIZE;|dp->db_free = dp->db_txt_start;"
 "ml_new_data|dp->db_line_count = 0;|dp->db_line_count = 1;"
 "ml_new_data|dp->db_id = DATA_ID;|dp->db_id = PTR_ID;"
 "ml_new_ptr|pp->pb_count = 0;|pp->pb_count = 1;"
 "ml_new_ptr|pp->pb_count_max = PB_COUNT_MAX(mfp);|pp->pb_count_max = PB_COUNT_MAX(mfp) + 1;"
 "ml_add_stack|buf->b_ml.ml_stack_size += STACK_INCR;|buf->b_ml.ml_stack_size += 0;"
 "ml_add_stack|  return top;|  return top + 1;"
 "ml_add_stack|  if (top == buf->b_ml.ml_stack_size) {|  if (top > buf->b_ml.ml_stack_size) {"
 "mf_rem_free|  mfp->mf_free_first = hp->bh_data;|  mfp->mf_free_first = hp;"
 "mf_ins_free|  hp->bh_data = mfp->mf_free_first;|  hp->bh_data = NULL;"
 "mf_need_trans|mfp->mf_neg_count > 0;|mfp->mf_neg_count >= 0;"
 "mf_alloc_bhdr|  hp->bh_page_count = page_count;|  hp->bh_page_count = page_count - 1;"
 "mf_free_bhdr|  xfree(hp->bh_data);|  xfree(hp);"
 "mf_free_fnames|  XFREE_CLEAR(mfp->mf_ffname);|  xfree(mfp->mf_ffname);"
 "ml_flush_deleted_bytes|  buf->deleted_codeunits = 0;|  buf->deleted_bytes2 = 0;"
 "ml_flush_deleted_bytes|  *codeunits = buf->deleted_codeunits;|  *codeunits = buf->deleted_codepoints;"
 "ml_add_deleted_len_buf|  if (len == -1 || len > maxlen) {|  if (len == -1) {"
 "ml_add_deleted_len_buf|  buf->deleted_bytes2 += (size_t)len + 1;|  buf->deleted_bytes2 += (size_t)len;"
 "ml_add_deleted_len_buf|    buf->deleted_codeunits++;|    buf->deleted_codepoints++;"
 "ml_add_deleted_len_buf|  if (inhibit_delete_count) {|  if (!inhibit_delete_count) {"
 "ml_get_buf_mut|  return ml_get_buf_impl(buf, lnum, true);|  return ml_get_buf_impl(buf, lnum, false);"
 "ml_get_pos|  return ml_get_buf(curbuf, pos->lnum) + pos->col;|  return ml_get_buf(curbuf, pos->lnum + 1) + pos->col;"
 "ml_get_pos_len|  return ml_get_buf_len(curbuf, pos->lnum) - pos->col;|  return ml_get_buf_len(curbuf, pos->lnum) - pos->col - 1;"
 "ml_append|  return ml_append_flags(lnum, line, len, newfile ? ML_APPEND_NEW : 0);|  return ml_append_flags(lnum, line, len, newfile ? 0 : ML_APPEND_NEW);"
 "ml_replace|  return ml_replace_buf(curbuf, lnum, line, copy, false);|  return ml_replace_buf(curbuf, lnum, line, copy, true);"
 "ml_timestamp|  ml_upd_block0(buf, UB_FNAME);|  ml_upd_block0(buf, UB_SAME_DIR);"
 "ml_delete|  return ml_delete_flags(lnum, 0);|  return ml_delete_flags(lnum - 1, 0);"
 "ml_line_alloced|  return curbuf->b_ml.ml_flags & ML_LINE_DIRTY;|  return curbuf->b_ml.ml_flags & 0x01;"
)
export PATH=$HOME/.vpipe/bin:$PATH
for m in "${M[@]}"; do
  IFS='|' read -r f from to <<< "$m"
  python3 -I - "$W/base.c" "$W/m.c" "$from" "$to" <<'PY'
import sys; s=open(sys.argv[1]).read(); assert s.count(sys.argv[3])==1, sys.argv[3]
open(sys.argv[2],"w").write(s.replace(sys.argv[3],sys.argv[4]))
PY
  (cd "$W" && frama-c -machdep x86_64 -cpp-extra-args="-I $HERE/../../memory/wp/stubs" m.c -wp -wp-fct "$f" -wp-rte -warn-unsigned-overflow -wp-model Typed+Cast \
     -wp-prover z3,cvc5 -wp-timeout 10 -wp-par "$(nproc)" -wp-cache none > m.log 2>&1)
  if grep -qE "Proved goals: +([0-9]+) / \1$" "$W/m.log"; then echo "SURVIVED $f: $to"; bad=1; else echo "caught   $f: $to"; fi
done
exit $bad
