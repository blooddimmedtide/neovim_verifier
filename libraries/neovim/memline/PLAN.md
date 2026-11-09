# memline.c / memfile.c verification plan

Claim: neovim_verifier draft PR #9 (branch claude/project-thread-kiwgsl).
Pinned upstream: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. Tool: Frama-C 33 WP
(z3, cvc5), model Typed+Cast, RTE guards, unsigned-overflow warnings, smoke tests on.

**Not finished.** 25 of 104 functions proved; 79 still unverified (list below).

## Status (2026-11-09, session stopped at the 09:00 UTC deadline)

- Proved with WP, every goal, smoke tests pass (no dead code or vacuous contracts): mf_alloc_bhdr, mf_free_bhdr, mf_free_fnames, mf_ins_free, mf_need_trans, mf_new_page_size, mf_rem_free, mf_set_fnames, ml_add_deleted_len, ml_add_deleted_len_buf, ml_add_stack, ml_flush_deleted_bytes, ml_get, ml_get_buf, ml_get_buf_mut, ml_get_pos, ml_get_pos_len, ml_line_alloced, ml_new_data, ml_new_ptr.
  Results: wp/results.txt (plus one helper lemma, proved). Planted bugs: wp/mutants.sh, 21/21 caught (wp/mutants_results.txt).
- Proved with CBMC 6.11 (bounds, pointer, overflow and shift checks, unwinding assertions, signed and
  unsigned char): b0_magic_wrong, char_to_long, long_to_char, ml_check_b0_id, ml_check_b0_strings. Specs in cbmc/harness.c and cbmc/harness_b0.c. Planted bugs:
  cbmc/mutants.sh, 8/8 caught. Trusted: a C-standard memchr in cbmc/prelude.h (CBMC has no model).
- Not done yet from the AGENT_PROMPT gates: independent adversarial review (REVIEW.md, mutants.toml),
  differential test, --unsigned-char run (these functions do no char arithmetic, but the gate is still open),
  CLAIM.md, vpipe.toml target, status.tsv rows.
- No bug found in the proved helpers.

## How to run

    bash wp/run_wp.sh <neovim checkout at 7b87ce8> [timeout] [function...]
    bash wp/mutants.sh <neovim checkout at 7b87ce8>
    bash cbmc/run_cbmc.sh <neovim checkout at 7b87ce8>
    bash cbmc/mutants.sh <neovim checkout at 7b87ce8>

ACSL contracts are on prototypes in wp/prelude.h; build.py copies each function body verbatim
(sha256 pinned) and checks the copied type/macro lines against upstream.

## Trusted contracts (prelude.h, "trusted" section)

- xmalloc / xrealloc / xfree (memory.c): never NULL, allocates, frees logged in order. xrealloc's
  byte preservation is stated for infoptr_T elements (24 bytes), which follows from preserving bytes.
- mf_new (memfile.c, not yet proved): returns a header plus a block whose DataBlock/PointerBlock header
  fields are valid and separate. Requires page_count >= 1 and mf_page_size >= 24
  (MIN_SWAP_PAGE_SIZE is 1048; ml_recover only accepts a page size >= the guessed one).
- FullName_save (path.c): a new allocation or NULL.
- ml_get_buf_impl / ml_get_buf_len (memline.c, not yet proved): return line text vp_line(buf, lnum, will_change)
  (uninterpreted) with vp_len readable bytes before the NUL. The ml_get* wrappers are proved against these.
- strlen: C-standard contract from ../memory/wp/stubs/vp_string.h. mb_utflen (mbyte.c): adds uninterpreted
  per-byte-range counts vp_cps / vp_cus (the spec of ml_add_deleted_len_buf is stated in terms of them).
- Reduced types: memfile_T without its two maps, buf_T with only b_ml.ml_stack/top/size.

## Preconditions taken from callers (to list in CLAIM.md)

- ml_new_data: 1 <= page_count and page_count * mf_page_size <= UINT_MAX. ml_append_int computes
  page_count from an int line length, so the block size stays below 2^31 + one page.
- ml_new_ptr: pb_count_max equals the exact entry count only when it fits in uint16_t
  (pages under about 1.5 MiB). Normal page sizes are at most MAX_SWAP_PAGE_SIZE (50000).
- ml_add_stack: 0 <= top <= size <= INT_MAX - 5, stack is its own allocation.
- ml_get_pos / ml_get_pos_len: 0 <= pos->col <= line length (callers keep positions inside the line;
  otherwise the pointer arithmetic / subtraction is out of range).
- mf_rem_free: free list not empty (documented: "Caller must check").
- ml_add_deleted_len(_buf): len >= -1 (callers pass -1 or a line length), the counters do not wrap,
  the string is at most PTRDIFF_MAX long. A len below -1 would wrap the counters, but no caller passes one.
- xrealloc: no "fresh w.r.t. every valid pointer" clause (that form is contradictory in WP, which
  ignores `allocates`; the same problem was found in the garray stub). Instead a ghost avoid object
  vp_avoid_buf (== buf in ml_add_stack's contract): the result is separate from that live object.

## Leads for the next session

- ml_recover: next target after the helpers (see the project's private notes before working on it).
- Lesson: a stub whose ensures says the result is valid must also say `allocates \result`, or WP treats
  the call as dead and proves anything after it. -wp-smoke-tests caught this (run_wp.sh now always uses it).

## Function list| file | function | status |
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
| memfile.c | mf_alloc_bhdr | proved (WP, review pending) |
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
| memline.c | ml_check_b0_id | proved (CBMC, both char signednesses, review pending) |
| memline.c | ml_check_b0_strings | proved (CBMC, both char signednesses, review pending) |
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
| memline.c | ml_get | proved (WP, against ml_get_buf_impl/ml_get_buf_len contracts; review pending) |
| memline.c | ml_get_buf | proved (WP, against ml_get_buf_impl/ml_get_buf_len contracts; review pending) |
| memline.c | ml_get_buf_mut | proved (WP, against ml_get_buf_impl/ml_get_buf_len contracts; review pending) |
| memline.c | ml_get_pos | proved (WP, against ml_get_buf_impl/ml_get_buf_len contracts; review pending) |
| memline.c | ml_get_len | not started |
| memline.c | ml_get_pos_len | proved (WP, against ml_get_buf_impl/ml_get_buf_len contracts; review pending) |
| memline.c | ml_get_buf_len | not started |
| memline.c | ml_region_text | not started |
| memline.c | gchar_pos | not started |
| memline.c | ml_get_buf_impl | not started |
| memline.c | ml_line_alloced | proved (WP, review pending) |
| memline.c | ml_append_int | not started |
| memline.c | ml_append_flush | not started |
| memline.c | ml_append | not started |
| memline.c | ml_append_flags | not started |
| memline.c | ml_append_buf | not started |
| memline.c | ml_add_deleted_len | proved (WP, review pending) |
| memline.c | ml_add_deleted_len_buf | proved (WP, review pending) |
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
| memline.c | ml_flush_deleted_bytes | proved (WP, review pending) |
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
| memline.c | b0_magic_wrong | proved (CBMC, both char signednesses, review pending) |
| memline.c | fnamecmp_ino | not started |
| memline.c | long_to_char | proved (CBMC, both char signednesses, review pending) |
| memline.c | char_to_long | proved (CBMC, both char signednesses, review pending) |
| memline.c | ml_setflags | not started |
| memline.c | ml_updatechunk | not started |
| memline.c | ml_find_line_or_offset | not started |
| memline.c | goto_byte | not started |
| memline.c | inc | not started |
| memline.c | incl | not started |
| memline.c | dec | not started |
| memline.c | decl | not started |
