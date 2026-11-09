# src/nvim/fold.c — claim (work in progress, NOT proved yet)

Pinned upstream: neovim/neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. Functions: 0 / 83 proved.

## foldFind (fold.c:1020-1049) — harness written, CBMC run pending

- Code under test: copied verbatim by `cbmc/extract.py`, sha256-pinned; only the types it uses are
  restated in `cbmc/fold_types.h`.
- Spec (`cbmc/spec.h`, from the doc comment, not the code): empty array → `false`, `*fpp = NULL`.
  Otherwise returns `true` iff some fold has `fd_top <= lnum < fd_top + fd_len`, and then `*fpp`
  points at that fold; else `*fpp` points at the first fold that starts below `lnum`
  (`fp + #folds with fd_top <= lnum`, which may be one past the end, as documented).
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

## Blocked

CBMC is not installed in this session's container and installing it was refused, so
`cbmc/run_cbmc.sh` has not been run. Next agent: `bash tools/install.sh`, then
`bash libraries/neovim/fold/cbmc/run_cbmc.sh <neovim checkout>`, then the review/mutant gates.

## Still unverified

All 83 functions in fold.c, including foldFind (harness ready, not run).
