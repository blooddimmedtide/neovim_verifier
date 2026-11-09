# src/xdiff/xutils.c — work in progress (not a candidate yet)

Pinned: Neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd (vendored from git's xdiff; git master has
the same code for every function below). Fixed fork: blooddimmedtide/verified_neovim, one branch
per fix (see "Upstream"), merged locally as `xdiff-fixed-local` for the proofs.
Tools: CBMC 6.4.1 (`cbmc/run_cbmc.sh`, x86_64, signed and unsigned char, `--unwinding-assertions`);
Frama-C 33 WP (`wp/build_wp.py`, Typed+Cast, `-wp-rte`, Z3 + CVC5); Z3 bit-vector check of one
hash lemma (`wp/lemmas.py`).

## Spec source
What each function is for: its name and comment, how the rest of xdiff calls it, and git's
documentation of the whitespace options (`-w`, `-b`, `--ignore-space-at-eol`,
`--ignore-cr-at-eol`, `--ignore-blank-lines`). The reference for lines (`wp/build_wp.py`, the
`match` / `el` / `ev` / `hacc` definitions) says which bytes of a line count in each mode:
- `-w`: every non-space byte;
- `-b`: every non-space byte before the trailing whitespace, and one `' '` for each run of
  whitespace before it;
- `--ignore-space-at-eol`: every byte before the trailing whitespace;
- `--ignore-cr-at-eol`: every byte before the line end, which is `"\n"` or `"\r\n"` (a CR at the
  end of an incomplete last line stays, as the code's own comment says);
- no flag: every byte (comparison) / every byte before the newline (hash).
The strongest flag wins (`-w` > `-b` > eol > cr), as the code's comment says. Two lines match when
the bytes that count are equal, in order. The reference decides: whitespace is C `isspace`, which
for bytes 128..255 depends on the locale (modelled as an unknown but fixed set).

## Status per function (fixed code)

| Function | Status | Tool | Proved property |
|---|---|---|---|
| `xdl_bogosqrt` | proved | CBMC | `2^ceil(bits(n)/2)`, so `r*r/4 <= n < r*r`; 1 for `n <= 0` |
| `xdl_emit_diffrec` | proved | CBMC | one `out_line` call with {pre, line} and git's "No newline" marker iff the line does not end in `\n`; -1 iff the callback fails |
| `xdl_mmfile_first`, `xdl_mmfile_size` | proved | CBMC, WP | the buffer and its size |
| `xdl_cha_init` | proved | WP | an empty store, `nsize = icount * isize` |
| `xdl_cha_free` | proved | WP | frees every block of the list exactly once, in order, nothing else |
| `xdl_cha_alloc` | proved | CBMC + WP lemma | isize fresh writable bytes after every earlier item (next slot, or first slot of a new block appended to the list); NULL with the store unchanged only when a new block was needed and malloc failed |
| `xdl_guess_lines` | proved | WP | size / (mean length of the first `sample` lines) + 1 |
| `xdl_blankline` | proved | WP | with a whitespace flag: only whitespace; without: `""` or `"\n"` (upstream: any line of 1 byte, a bug) |
| `len_without_eol` (new, fix) | proved | WP | the line length without `"\n"` / `"\r\n"` |
| `xdl_recmatch` | OPEN (WP: every goal proved in some run except `sk_bd`, a case step of `-b`; one full run with all hints still to do) | WP | 1 iff the lines match in the mode of the flags, else 0 |
| `xdl_hash_record` | proved (no whitespace flag: WP 69/69; with a flag it calls `xdl_hash_record_with_whitespace`, which is OPEN) | WP | the hash of the record's counted bytes; `*data` moves past the record |
| `xdl_hash_record_with_whitespace` | OPEN (not run yet) | WP | as `xdl_hash_record` |
| `xdl_hashbits` | proved | CBMC | the least `b >= 1` with `2^b >= size` |
| `xdl_num_out` | OPEN (CBMC does not finish in 40 min: 64-bit division) | CBMC | the decimal text and NUL, its length; nothing after the NUL |
| `xdl_format_hunk_hdr` (via `xdl_emit_hunk_hdr`) | OPEN (waits on `xdl_num_out`) | CBMC | the unified-diff hunk header, function name cut so the line is at most 128 bytes |
| `xdl_emit_hunk_hdr` | proved (callback path) | CBMC | passes the hunk to `out_hunk` with the empty-side start rule; -1 iff it fails |
| `xdl_fall_back_diff` | proved | CBMC | re-diffs the two ranges as files and copies the line changes into the ranges; nothing changes on failure |

## Preconditions (each from the callers or the types)
- Record and line sizes are >= 0 and at most `INT_MAX` (they lie in an `mmfile_t`, whose size is int).
- `xdl_cha_init`: `isize * icount` fits in a long (callers: a struct size times `n / 4 + 1`).
- `xdl_cha_alloc`: the store came from `xdl_cha_init` and `xdl_cha_alloc`.
- `xdl_emit_hunk_hdr` text path: `func` has `funclen >= 0` readable bytes; `s - 1` must not overflow
  for an empty side (`s == LONG_MIN`).
- `xdl_fall_back_diff`: the ranges are within the files, and a file has fewer than `INT_MAX`
  records (`line1 + count1 - 2` is computed in int). xdl_do_diff (xdiffi.c) is used by its
  contract: it fails, or gives one `rchg` byte per record of each file.

## What the proofs rely on
- CBMC 6.4.1, Frama-C 33 WP / Why3 / Z3 / CVC5. The xmalloc model in `cbmc/memory.h`.
- Declared tool patches (text only), in `wp/build_wp.py`: the headers are replaced by the same
  types and macros; `XDL_ISSPACE` calls a model of `isspace((unsigned char)c)`; `xdl_free` calls a
  model that records its argument; the `-w` loop of `xdl_recmatch`, which WP cannot take because
  `goto skip_ws` enters it in the middle, is rotated into a loop with the same statements in the
  same order.
- `hash_step` (one hash step as the C code computes it) and `ws_bits` (`XDF_WHITESPACE_FLAGS`,
  30, is the four bits 2, 4, 8, 16 of a long) are checked by Z3 over 80-bit bit-vectors
  in `wp/lemmas.py` and used by WP as hypotheses. All other ACSL lemmas are WP-proved; the
  `lem_*` ghost functions are proved induction steps, not assumptions.

## Upstream
- `xdl_blankline`: a one-character last line counts as blank, so `vim.diff('x', 'y',
  {ignore_blank_lines = true})` returns no hunk (findings/xdiff-blankline-one-char-last-line.md).
- `xdl_num_out`: negative numbers print as "5-", and -LONG_MIN overflows; `xdl_recmatch`: int
  indexes overflow on lines of 2 GiB; `xdl_recmatch` with only ignore-cr-at-eol matches "a\r"
  and "a\r\n" (findings/xdiff-xutils-minor.md). Not reachable from Neovim as far as we can tell.
