# register.c / ops.c

Pinned upstream: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. 101 functions (register.c 53, ops.c 48).
Claimed by thread "Verify Neovim registers and ops" (2026-11-09). Progress and the list of
unverified functions are kept here.

## Progress (2026-11-09): 18 / 101 functions proved

- WP (`wp/run_wp.sh`): get_extra_op_char, get_op_char, get_op_type, get_vts, get_y_previous, get_y_register, op_is_change, op_on_lines, op_redoable, op_reg_amount, op_reg_get, op_reg_set_previous, op_self_select.
- CBMC (`cbmc/run_cbmc.sh`): get_unname_register, op_global_reg_iter, op_reg_iter, valid_yank_reg.
- Fixed and proved: get_vts_sum (finding `findings/vts-sum-overflow.md`, fix verified_neovim 09421b0).
- Planted bugs (`run_mutants.py`, chosen by this session): 23/23 caught for the WP functions; CBMC harnesses: `cbmc/run_mutants.py`, 7/7 quick ones caught (op_reg_iter ones: see below).
- Not yet: independent review (and reviewer-chosen mutants), CI run.

## Unverified (83)
- ops.c:op_shift
- ops.c:get_new_sw_indent
- ops.c:get_new_vts_indent
- ops.c:shift_line
- ops.c:shift_block
- ops.c:block_insert
- ops.c:op_delete
- ops.c:mb_adjust_opend
- ops.c:pbyte
- ops.c:replace_character
- ops.c:op_replace
- ops.c:op_tilde
- ops.c:swapchars
- ops.c:swapchar
- ops.c:op_insert
- ops.c:op_change
- ops.c:adjust_cursor_eol
- ops.c:skip_comment
- ops.c:do_join
- ops.c:reset_lbr
- ops.c:restore_lbr
- ops.c:block_prep
- ops.c:getregionpos_prep
- ops.c:getregionpos_line
- ops.c:charwise_block_prep
- ops.c:op_addsub
- ops.c:do_addsub
- ops.c:clear_oparg
- ops.c:line_count_info
- ops.c:cursor_pos_info
- ops.c:op_colon
- ops.c:free_operatorfunc_option
- ops.c:set_ref_in_opfunc
- ops.c:op_function
- ops.c:get_op_vcol
- ops.c:is_ex_cmdchar
- ops.c:op_ins_visual
- ops.c:do_pending_operator
- ops.c:get_region_bytecount
- register.c:get_expr_register
- register.c:set_expr_line
- register.c:get_expr_line
- register.c:get_expr_line_src
- register.c:get_default_register_name
- register.c:reg_max_ts
- register.c:op_reg_set
- register.c:update_yankreg_width
- register.c:get_yank_register
- register.c:yank_register_mline
- register.c:copy_register
- register.c:stuff_yank
- register.c:do_record
- register.c:put_in_typebuf
- register.c:put_reedit_in_typebuf
- register.c:execreg_line_continuation
- register.c:do_execreg
- register.c:insert_reg
- register.c:get_spec_reg
- register.c:cmdline_paste_reg
- register.c:shift_delete_registers
- register.c:clear_registers
- register.c:free_register
- register.c:yank_copy_line
- register.c:op_yank_reg
- register.c:format_reg_type
- register.c:add_regtype_to_dict
- register.c:do_autocmd_textyankpost
- register.c:put_do_autocmd
- register.c:op_yank
- register.c:do_put
- register.c:dis_msg
- register.c:ex_display
- register.c:get_reg_type
- register.c:get_reg_wrap_one_line
- register.c:get_reg_contents
- register.c:init_write_reg
- register.c:str_to_reg
- register.c:finish_write_reg
- register.c:write_reg_contents
- register.c:write_reg_contents_lst
- register.c:write_reg_contents_ex
- register.c:prepare_yankreg_from_object
- register.c:finish_yankreg_from_object

## Next
- op_reg_set, free_register, clear_registers, set_expr_line need allocation stubs: use ghost
  "avoid" arguments as in typval/wp_blob, run with -wp-smoke-tests (the garray stub is
  contradictory, do not reuse it).
- shift_block / get_new_vts_indent / get_new_sw_indent: check the other indent arithmetic for
  the same overflow as get_vts_sum (shift_block computes total in int).
