# mark.c + marktree.c (claim)

Claimed by the "Verify Neovim marks code" thread, 2026-11-09. Pinned upstream: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd.
Tool: Frama-C WP (Typed+Cast, RTE, Z3/CVC5), tooling copied from garray/wp and hashtab/wp.

Inventory: mark.c 56 functions, marktree.c 82 functions (138 total). None is verified yet; this file lists progress.

## Order
1. marktree.c position algebra: pos_leq, pos_less, relative, unrelative, compose, key_cmp
   (key invariant: unrelative(base, relative(base, p)) == p, and order is preserved).
2. marktree.c intersection arrays: intersection_has, intersect_item_pos (sorted-array search).
3. marktree.c meta counters: meta_describe_key_inc, meta_describe_key, meta_has.
4. B-tree structural invariants (marktree_check_node as the spec), then insert/delete/split/merge.
5. mark.c.

## Progress (2026-11-09 ~08:15 UTC; thread stopped at the 09:00 UTC deadline)

marktree.c: 15 of 82 functions proved (14 candidate, meta_has fixed-candidate). See CLAIM.md.
mark.c: 4 of 56 proved (mark_view_make, mark_check_line_bounds, next_buffer_mark, mark_jumplist_iter; not yet reviewed). mark_global_iter in progress (25/43 goals).

### Still unverified: marktree.c (67)
refkey, id2node, split_node, marktree_putp_aux, marktree_put, intersect_node, unintersect_node, marktree_intersect_pair, marktree_alloc_node, meta_describe_node, marktree_put_key, marktree_del_itr, marktree_revise_meta, intersect_merge, intersect_mov, intersect_mov_test, intersect_common, intersect_add, intersect_sub, bubble_up, merge_node, kvi_move, pivot_right, pivot_left, marktree_clear, marktree_free_subtree, marktree_free_node, marktree_move, marktree_restore_pair, marktree_itr_get, marktree_itr_get_ext, marktree_itr_first, marktree_itr_last, marktree_itr_next, marktree_itr_next_skip, marktree_itr_get_filter, marktree_itr_step_out_filter, marktree_itr_next_filter, marktree_itr_check_filter, marktree_itr_prev, marktree_itr_current, marktree_itr_get_overlap, marktree_itr_step_overlap, check_damage, swap_keys, marktree_splice, marktree_move_region, marktree_lookup_ns, pseudo_index, pseudo_index_for_id, marktree_lookup, marktree_itr_set_node, marktree_get_altpos, marktree_get_alt, marktree_itr_fix_pos, marktree_put_test, mt_right_test, marktree_del_pair_test, marktree_check, marktree_check_node, marktree_check_intersections, mt_recurse_nodes, mt_recurse_nodes_compare, mt_inspect, mt_dbg_id, mt_inspect_node, mt_inspect_dotfile_node

### Still unverified: mark.c (52)
setmark, free_fmark, free_xfmark, clear_fmark, do_markset_autocmd, setmark_pos, mark_jumplist_forget_file, mark_forget_file, setpcmark, checkpcmark, get_jumplist, get_changelist, mark_get, mark_get_global, mark_get_local, mark_get_motion, mark_get_visual, pos_to_mark, switch_to_mark_buf, mark_move_to, mark_view_restore, getnextmark, fname2fnum, fmarks_check_names, fmarks_check_one, mark_check, clrallmarks, fm_getname, mark_line, ex_marks, ex_delmarks, ex_jumps, ex_clearjumps, ex_changes, mark_adjust, mark_adjust_nofold, mark_adjust_buf, mark_col_adjust, cleanup_jumplist, copy_jumplist, mark_global_iter, mark_buffer_iter, mark_set_global, mark_set_local, free_jumplist, set_last_cursor, free_all_marks, mark_mb_adjustpos, add_mark, get_buf_local_marks, get_raw_global_mark, get_global_marks

### Next steps
- B-tree invariant predicate (from marktree_check_node: key order inside a node and across children with
  relative positions, child counts n in [T-1, 2T-1] except the root, parent/p_idx links, level, meta sums,
  id2node consistency), then split_node, marktree_putp_aux, marktree_put_key, merge_node, pivot_left/right,
  marktree_del_itr. id2node/refkey need a ghost model of the pmap (map.c is claimed by PR #8).
- Iterators need the same invariant plus the iterator stack (s[], lvl, pos).
- mark.c is mostly buffer/window state; prove the pure helpers first (mark_check_line_bounds, pos_to_mark,
  fm_getname, mark_mb_adjustpos needs mbyte, which is proved).
