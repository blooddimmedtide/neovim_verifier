# src/xdiff/xutils.c (claimed, work in progress)

Claimed by the "Verify Neovim bundled libraries" thread. Nothing is proved yet.

Functions (18): xdl_bogosqrt, xdl_emit_diffrec, xdl_mmfile_first, xdl_mmfile_size, xdl_cha_init,
xdl_cha_free, xdl_cha_alloc, xdl_guess_lines, xdl_blankline, ends_with_optional_cr, xdl_recmatch,
xdl_hash_record_with_whitespace, xdl_hash_record, xdl_hashbits, xdl_num_out, xdl_format_hunk_hdr,
xdl_emit_hunk_hdr, xdl_fall_back_diff.
Plan: CBMC for the byte-level helpers (independent reference in spec.h, exact-size objects,
both char signednesses), Frama-C WP for loops over unbounded records, differential test.
