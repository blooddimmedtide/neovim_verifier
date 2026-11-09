# src/nvim/linematch.c (pinned upstream 7b87ce8): 3 of 10 proved (bounded), 7 open

| Function | Tool | Status |
|---|---|---|
| line_len | CBMC, N<=4 | candidate (bounded; WP for all sizes still to do) |
| fastforward_buf_to_lnum | CBMC, N<=4 | candidate (bounded) |
| matching_chars_iwhite | CBMC, N<=2 | fixed-candidate (over-read finding, fix proved bounded) |
| matching_chars | CBMC | open: harness OOM, needs WP (LCS invariant) |
| count_n_matched_chars | CBMC | open: harness written, not run |
| try_possible_paths | WP | open |
| unwrap_indexes | WP | open |
| populate_tensor | WP | open |
| linematch_nbuffers | WP | open |
| test_charmatch_paths | WP | open |

Run: `bash cbmc/run_cbmc.sh <neovim tree>` (N=4 default; use N=2 for the matching_chars* harnesses).
