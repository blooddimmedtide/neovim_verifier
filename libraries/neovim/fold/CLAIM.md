# src/nvim/fold.c — claim (work in progress)

Pinned upstream: neovim/neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. Functions: 1 / 83 proved within a bound (foldFind, see below); 0 / 83 proved for all sizes.

## foldFind (fold.c:1020-1049) — CBMC: proved for arrays of 0..6 folds

- Code under test: copied verbatim by `cbmc/extract.py`, sha256-pinned; only the types it uses are
  restated in `cbmc/fold_types.h`.
- Spec (`cbmc/spec.h`, from the doc comment, not the code): empty array → `false`, `*fpp = NULL`.
  Otherwise returns `true` iff some fold has `fd_top <= lnum < fd_top + fd_len`, and then `*fpp`
  points at that fold; else `*fpp` points at the first fold that starts below `lnum`
  (`fp + #folds with fd_top <= lnum`, which may be one past the end, as documented).
- Result (CBMC 6.4.1, 2026-11-09): `bash cbmc/run_cbmc.sh <neovim>` proves all 14 runs
  (n = 0..6 folds, signed and unsigned char), every lnum and every fold contents, no bounds,
  pointer or signed-overflow failure, unwinding assertions on. This is a bounded proof: arrays of
  more than 6 folds are not covered (binary search needs about log2(n) steps; a WP proof with a
  loop invariant would cover all sizes).
- Planted bugs, chosen by me, not yet by an independent reviewer: 6 of 6 non-equivalent
  mutants caught (`<=`→`<` in the loop, `high = i`, `low = i`, `fp + high` at the end,
  `>`→`>=` on fd_top, `<=`→`<` on the fold end). `*fpp = fp` instead of `NULL` for an empty
  array is equivalent in the harness (ga_data is NULL there).
- Removing the `fd_top + fd_len <= INT32_MAX` precondition makes CBMC report the signed
  overflow in `fp[i].fd_top + fp[i].fd_len` (fold.c:1039), so that precondition is needed.
- Harness (`cbmc/harness.c`): every fold array of 0..6 folds (exact-size heap object, so any
  out-of-bounds read fails), every `lnum`, both char signednesses, x86_64, overflow checks on,
  `--unwinding-assertions`.
- Preconditions (the documented fold-array invariant, fold.c:62-65, kept by every insertion site):
  `fd_len >= 1`, `fd_top >= 0`, folds sorted by `fd_top` and non-overlapping, and
  `fd_top + fd_len <= INT32_MAX`.
  Note: the last condition is not automatic. A fold that ends on line `MAXLNUM` (2^31 - 1) gives
  `fd_top + fd_len == 2^31`, a signed overflow in `fp[i].fd_top + fp[i].fd_len`. That needs a
  2^31-line buffer, so it is recorded here, not yet as a finding; to be checked against how
  folds are clipped at the buffer end.
- Evidence so far: differential test (`cbmc/run_difftest.sh`), gcc -O2 with ASan+UBSan, both
  signednesses, exhaustive over all valid arrays of up to 4 folds with tops 0..12 and lengths 1..4
  and every lnum in -2..14, plus edges near INT32_MAX: 778,279 cases, 0 mismatches.
  This is testing, not a proof.

## Next

Check whether a fold can end on line MAXLNUM (finding or not); independent review and
`mutants.toml`; `[targets.*]` entry in vpipe.toml and status.tsv row; WP proof for all sizes.

## Still unverified

82 of 83 functions in fold.c (every function except foldFind), and foldFind beyond 6 folds.
