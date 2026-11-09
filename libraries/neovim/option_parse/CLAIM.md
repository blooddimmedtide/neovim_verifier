# CLAIM: `:set` argument scanners in src/nvim/option.c

Source: `src/nvim/option.c` at verified_neovim `7b87ce8` (pinned by `cbmc/pins.sha256`;
`cbmc/extract.sh <tree>` re-extracts verbatim and checks the pin). Tool: CBMC 5.95.1.
Strength: **bounded** model check (all strings in buffers up to 16 bytes, both char signednesses;
up to 64 bytes signed char), plus an exhaustive differential test of the compiled code.

| function | property | status |
|---|---|---|
| `get_op` | returns `+=`/`^=`/`-=` operator from the first two chars, else `OP_NONE`; never reads past the NUL | candidate |
| `get_option_prefix` | `no` prefix (skip 2) wins over `inv` (skip 3), else `PREFIX_NONE` with the pointer unchanged; no OOB | candidate |
| `find_tty_option_end` | end of `term`, `ttytype` (whole string), `t_xx`, `<t_xx>`, `<...>` names, else NULL; no OOB | candidate |
| `is_tty_option` | true exactly when `find_tty_option_end` finds a name | candidate |
| `find_option_end` | tty name: its end, index kOptInvalid, no lookup; no leading ASCII letter: NULL, kOptInvalid; else end of the letter run, looked up once with exactly (arg, run length). `find_option_len` is a stub, not proved | candidate (name scan only) |

## What the reference (`cbmc/spec.h`) decides itself
- `term`/`ttytype` match only the whole string (the code uses `strequal`), so `termx` is not a tty name.
- `<t_xx` without `>` is NULL; `<t_>` and `<>` are bracketed names ending after the first `>`.
- `get_op("")` is `OP_NONE` and must not read `arg[1]`.

## Harness assumptions
- Input is a NUL-terminated string in an object of exactly `n` bytes (documented: callers pass
  the `:set` argument string). Earlier NULs are allowed.
- `strequal` is copied from `memory.c` (already a separate proof target).

## Evidence
- `cbmc/run.sh 16`: 702/702 properties, signed and `--unsigned-char` (`cbmc_result.txt`).
- `cbmc/run.sh 64`: signed char, 548/548 before `is_tty_option` was added (`cbmc_result_64.txt`).
- `cbmc/difftest.c`: gcc -O2, ASan+UBSan, both signednesses, all 1,118,481 strings of length 0..5
  over a 16-char alphabet that hits every branch: 0 mismatches (does not exercise `find_option_end`).
- `cbmc/mutants.sh`: 17/17 planted bugs caught (`mutants_result.txt`).

## Not done (deadline 2026-11-09 09:00 UTC)
- Unbounded proof of `find_tty_option_end`'s `>` search loop (WP); bounded only here.
- Independent adversarial review (REVIEW.md) and CI target in vpipe.toml.
- `find_option_len` (options[] hash lookup) is not proved; the stub returns an arbitrary index.
- No bug found in these five functions.
