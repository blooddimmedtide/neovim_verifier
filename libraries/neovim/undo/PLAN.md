# src/nvim/undo.c (pinned upstream 7b87ce8, 83 functions)

Claimed by thread "Verify Neovim undo code" (2026-11-09). Start: undo-file read and serialize
helpers (the parsing attack surface of `:rundo` / 'undofile').

Progress and the list of unverified functions are kept below.

## Status (2026-11-09 08:15 UTC)

Proved (candidate, see CLAIM.md): undo_read, undo_read_string, undo_write, undo_write_bytes, put_header_ptr, serialize_pos,
serialize_visualinfo, undo_read_4c, undo_read_2c, undo_read_byte, undo_read_len, unserialize_pos,
unserialize_visualinfo, uhp_seq_cmp, uhp_table_find (WP, any size). Plus callees get2c, get4c of
fileio.c.

Fixed-candidate: undo_read_time (get8ctime signed shift overflow; fix in verified_neovim PR #8).

Still unverified (67 of 83): u_check_tree, u_check, u_save_cursor, u_save, u_save_buf, u_savesub, u_inssub, u_savedel, undo_allowed, get_undolevel, zero_fmark_additional_data, u_savecommon, u_entry_resized, u_compute_hash, u_get_undo_file_name, corruption_error, u_free_uhp, serialize_header, serialize_uhp, unserialize_uhp, serialize_extmark, unserialize_extmark, serialize_uep, unserialize_uep, u_write_undo, u_read_undo, u_undo, u_redo, u_undo_and_forget, u_doit, undo_time, u_undoredo, u_undo_end, undo_fmt_time, u_sync, ex_undolist, ex_undojoin, u_unchanged, u_find_first_changed, u_update_save_nr, u_unch_branch, u_get_headentry, u_getbot, u_freeheader, u_freebranch, u_forget_header, u_freeentries, u_freeentry, u_forget_unchanged, u_clearall, u_blockfree, u_clearallandblockfree, u_saveline, u_clearline, u_undoline, u_save_line, u_save_line_buf, bufIsChanged, anyBufIsChanged, curbufIsChanged, u_eval_tree, f_undofile, f_undotree, u_update_named_mark, u_force_get_undo_header, u_checkpoint, u_rollback

Next: the record readers that use these helpers (unserialize_extmark, unserialize_uep,
unserialize_uhp, then u_read_undo), then the matching serializers. Independent review + planted
bugs for the proved set.

## Stopped 2026-11-09 08:35 UTC (usage deadline)

- Review done (REVIEW.md, accept with changes; fixes applied), 22/22 planted bugs caught.
- Work in progress, NOT counted: `cbmc/harness_uep.c` + `run_uep.sh` (bounded unserialize_uep /
  serialize_uep incl. a round trip). The round-trip harness proved once (unsigned char); the
  reader harness ran out of memory (exit 137) even at UEP_MAX=1. Next: split the reader harness
  per error path, or do unserialize_uep in WP using the proved helper contracts.
