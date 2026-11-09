# memline.c / memfile.c verification plan

Claim: neovim_verifier draft PR #9 (branch claude/project-thread-kiwgsl).
Pinned upstream: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. Tool: Frama-C 33 WP
(z3, cvc5), model Typed+Cast, RTE guards, unsigned-overflow warnings, smoke tests on.

**Not finished.** 10 of 104 functions proved; 94 still unverified (list below).

## Status (2026-11-09, session stopped at the 09:00 UTC deadline)

- Proved, every goal, smoke tests pass (no dead code/vacuous contracts): mf_free_bhdr, mf_free_fnames, mf_ins_free, mf_need_trans, mf_new_page_size, mf_rem_free, mf_set_fnames, ml_add_stack, ml_new_data, ml_new_ptr.
  Results: wp/results.txt. Planted bugs: wp/mutants.sh (14 mutants), results in wp/mutants_results.txt.
- Not done yet from the AGENT_PROMPT gates: independent adversarial review (REVIEW.md, mutants.toml),
  differential test, --unsigned-char run (these functions do no char arithmetic, but the gate is still open),
  CLAIM.md, vpipe.toml target, status.tsv rows.
- No bug found in the proved helpers.

## How to run

    bash wp/run_wp.sh <neovim checkout at 7b87ce8> [timeout] [function...]
    bash wp/mutants.sh <neovim checkout at 7b87ce8>

ACSL contracts are on prototypes in wp/prelude.h; build.py copies each function body verbatim
(sha256 pinned) and checks the copied type/macro lines against upstream.

## Trusted contracts (prelude.h, "trusted" section)

- xmalloc / xrealloc / xfree (memory.c): never NULL, allocates, frees logged in order. xrealloc's
  byte preservation is stated for infoptr_T elements (24 bytes), which follows from preserving bytes.
- mf_new (memfile.c, not yet proved): returns a header plus a block whose DataBlock/PointerBlock header
  fields are valid and separate. Requires page_count >= 1 and mf_page_size >= 24
  (MIN_SWAP_PAGE_SIZE is 1048; ml_recover only accepts a page size >= the guessed one).
- FullName_save (path.c): a new allocation or NULL.
- Reduced types: memfile_T without its two maps, buf_T with only b_ml.ml_stack/top/size.

## Preconditions taken from callers (to list in CLAIM.md)

- ml_new_data: 1 <= page_count and page_count * mf_page_size <= UINT_MAX. ml_append_int computes
  page_count from an int line length, so the block size stays below 2^31 + one page.
- ml_new_ptr: pb_count_max equals the exact entry count only when it fits in uint16_t
  (pages under about 1.5 MiB). Normal page sizes are at most MAX_SWAP_PAGE_SIZE (50000).
- ml_add_stack: 0 <= top <= size <= INT_MAX - 5, stack is its own allocation.
- mf_rem_free: free list not empty (documented: "Caller must check").

## Leads for the next session

- ml_recover: next target after the helpers (see the project's private notes before working on it).
- Lesson: a stub whose ensures says the result is valid must also say `allocates \result`, or WP treats
  the call as dead and proves anything after it. -wp-smoke-tests caught this (run_wp.sh now always uses it).

## Function list

| file | function | status |
|---|---|---|
| memfile.c | mf_open | not started |
| memfile.c | mf_open_file | not started |
| memfile.c | mf_close | not started |
| memfile.c | mf_close_file | not started |
| memfile.c | mf_new_page_size | proved (WP, review pending) |
| memfile.c | mf_new | not started |
| memfile.c | mf_get | not started |
| memfile.c | mf_put | not started |
| memfile.c | mf_free | not started |
| memfile.c | mf_sync | not started |
| memfile.c | mf_set_dirty | not started |
| memfile.c | mf_release_all | not started |
| memfile.c | mf_alloc_bhdr | open: 20/21 goals; open: the size_t product (size_t)mf_page_size * page_count equals the exact product (nonlinear, SMT times out). Needs a bvlemmas.py-style lemma. |
| memfile.c | mf_free_bhdr | proved (WP, review pending) |
| memfile.c | mf_ins_free | proved (WP, review pending) |
| memfile.c | mf_rem_free | proved (WP, review pending) |
| memfile.c | mf_read | not started |
| memfile.c | mf_write | not started |
| memfile.c | mf_trans_add | not started |
| memfile.c | mf_trans_del | not started |
| memfile.c | mf_free_fnames | proved (WP, review pending) |
| memfile.c | mf_set_fnames | proved (WP, review pending) |
| memfile.c | mf_fullname | not started |
| memfile.c | mf_need_trans | proved (WP, review pending) |
| memfile.c | mf_do_open | not started |
| memline.c | ml_open | not started |
| memline.c | ml_setname | not started |
| memline.c | ml_open_files | not started |
| memline.c | ml_open_file | not started |
| memline.c | check_need_swap | not started |
| memline.c | ml_close | not started |
| memline.c | ml_close_all | not started |
| memline.c | ml_close_notmod | not started |
| memline.c | ml_timestamp | not started |
| memline.c | ml_check_b0_id | not started |
| memline.c | ml_check_b0_strings | not started |
| memline.c | ml_upd_block0 | not started |
| memline.c | set_b0_fname | not started |
| memline.c | set_b0_dir_flag | not started |
| memline.c | add_b0_fenc | not started |
| memline.c | swapfile_proc_running | not started |
| memline.c | ml_recover | not started |
| memline.c | recover_names | not started |
| memline.c | make_percent_swname | not started |
| memline.c | swapfile_dict | not started |
| memline.c | swapfile_info | not started |
| memline.c | swapfile_unchanged | not started |
| memline.c | recov_file_names | not started |
| memline.c | ml_sync_all | not started |
| memline.c | ml_preserve | not started |
| memline.c | ml_get | not started |
| memline.c | ml_get_buf | not started |
| memline.c | ml_get_buf_mut | not started |
| memline.c | ml_get_pos | not started |
| memline.c | ml_get_len | not started |
| memline.c | ml_get_pos_len | not started |
| memline.c | ml_get_buf_len | not started |
| memline.c | ml_region_text | not started |
| memline.c | gchar_pos | not started |
| memline.c | ml_get_buf_impl | not started |
| memline.c | ml_line_alloced | not started |
| memline.c | ml_append_int | not started |
| memline.c | ml_append_flush | not started |
| memline.c | ml_append | not started |
| memline.c | ml_append_flags | not started |
| memline.c | ml_append_buf | not started |
| memline.c | ml_add_deleted_len | not started |
| memline.c | ml_add_deleted_len_buf | not started |
| memline.c | ml_replace | not started |
| memline.c | ml_replace_len | not started |
| memline.c | ml_replace_buf | not started |
| memline.c | ml_replace_buf_len | not started |
| memline.c | ml_delete_buf | not started |
| memline.c | ml_delete_int | not started |
| memline.c | ml_delete | not started |
| memline.c | ml_delete_flags | not started |
| memline.c | ml_setmarked | not started |
| memline.c | ml_firstmarked | not started |
| memline.c | ml_clearmarked | not started |
| memline.c | ml_flush_deleted_bytes | not started |
| memline.c | ml_flush_line | not started |
| memline.c | ml_new_data | proved (WP, review pending) |
| memline.c | ml_new_ptr | proved (WP, review pending) |
| memline.c | ml_find_line | not started |
| memline.c | ml_add_stack | proved (WP, review pending) |
| memline.c | ml_lineadd | not started |
| memline.c | resolve_symlink | not started |
| memline.c | makeswapname | not started |
| memline.c | get_file_in_dir | not started |
| memline.c | attention_message | not started |
| memline.c | do_swapexists | not started |
| memline.c | findswapname | not started |
| memline.c | b0_magic_wrong | not started |
| memline.c | fnamecmp_ino | not started |
| memline.c | long_to_char | not started |
| memline.c | char_to_long | not started |
| memline.c | ml_setflags | not started |
| memline.c | ml_updatechunk | not started |
| memline.c | ml_find_line_or_offset | not started |
| memline.c | goto_byte | not started |
| memline.c | inc | not started |
| memline.c | incl | not started |
| memline.c | dec | not started |
| memline.c | decl | not started |
