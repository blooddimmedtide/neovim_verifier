# Claim: src/nvim/linematch.c (in progress, NOT finished)

Pinned upstream 7b87ce8 (sha256 7e70347a...f492); fix verified_neovim e5db114 (sha256 f11b98b1...affe).
Function bodies are copied verbatim by `cbmc/build.py`, checked against these pins.

## Proved (CBMC 6.4.1, x86_64, signed and unsigned char, bounds/pointer/overflow/conversion
checks, `--unwinding-assertions`). These are BOUNDED proofs: buffer sizes up to N bytes.

| Function | Property (reference in `cbmc/spec.h`, from the doc comments) | Bound | Status |
|---|---|---|---|
| line_len | equals bytes before the first `'\n'` in ptr[0..size), else size | N=4 | candidate (bounded) |
| fastforward_buf_to_lnum | returns the text after the (lnum-1)-th newline; `{NULL, 0}` if it runs out; lnum <= 0 returns input | N=4, any lnum > INT32_MIN | candidate (bounded) |
| matching_chars_iwhite | equals LCS of the two first lines with ' ' and '\t' removed (lines < 799 bytes) | N=2 | fixed-candidate: upstream fails (over-read), fix proved |

Relies on: a memchr model written from C11 7.24.5.1 (in `cbmc/harness.c`); precondition
lnum > INT32_MIN for fastforward_buf_to_lnum (`lnum - 1` overflows otherwise; callers pass
line numbers >= 1). The 799-byte cap is not exercised by these bounds.

## Not proved
- matching_chars: direct harness ran out of memory at N=2 and N=3 (covered indirectly only for
  blank-free inputs through matching_chars_iwhite at N=2).
- count_n_matched_chars: harness written (`h_count_n`), not run.
- try_possible_paths, unwrap_indexes, populate_tensor, linematch_nbuffers, test_charmatch_paths:
  not started (recursion over diff tensors; need WP with invariants).
- No unbounded (WP) proof yet, no differential test, no planted bugs, no independent review.
