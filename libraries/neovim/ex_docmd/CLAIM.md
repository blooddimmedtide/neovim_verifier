# Claim: ex_docmd.c command-separator and command-name helpers

**Status:** candidate (machine checks pass; no independent review yet; owner sign-off pending).
**Upstream:** neovim/neovim `7b87ce822e6fd45a4d9993599c2854afdb0dc4dd`, `src/nvim/ex_docmd.c`.
**Tool:** CBMC 6.4.1, x86_64, both `char` signednesses.
**Strength:** bounded. Every string up to 7 characters (8-byte objects, with all shorter
strings covered because any byte may be NUL) and every `int` value. Not a proof for longer
strings; a Frama-C WP proof for unbounded length is the next step.

## Functions

| Function | Line | Property proved (against `cbmc/spec.h`) |
|---|---|---|
| `ends_excmd` | 4631 | non-zero exactly for NUL, `\|`, `"`, `\n`; every `int` |
| `find_nextcmd` | 4638 | pointer just past the first `\|` or `\n`, NULL when none; no read past the NUL |
| `check_nextcmd` | 4652 | after blanks, `\|` or `\n` gives the next byte, else NULL |
| `skip_colon_white` | 1213 | skips the leading colons and blanks after each (and leading blanks when asked) |
| `checkforcmd` | 2991 | match iff at least `len` chars of `cmd` match and the next char is no letter; `*pp` moved past blanks on a match, unchanged otherwise; for every `int len` |

`skipwhite` (charset.c, claimed by PR #3) is extracted verbatim and checked against its own
spec here, but its status row belongs to that PR.

Every proof also checks memory safety (bounds, pointer, overflow, conversion) and
`--unwinding-assertions`. Exception: `checkforcmd` runs without `--conversion-check`, because
`ASCII_ISALPHA` casts a possibly negative `char` to `unsigned`, which is defined (modular)
behavior in C; signed overflow is still checked.

## What the reference decides itself
- `checkforcmd` with `len` larger than `strlen(cmd)` or negative: the reference follows the
  documented rule literally (never matches when `len > strlen(cmd)`; any non-letter tail matches when `len <= 0`).
- The comment in `checkforcmd` says "optional tail"; the reference reads it as "a prefix of
  `cmd` of length at least `len`".

## Assumptions
- Inputs are NUL-terminated strings (documented as C strings by every caller).
- Harness allocations succeed (`malloc != NULL` assumed in the harness only).

## Evidence
- `cbmc/run.sh <pinned tree>`: 36/36 runs succeed (`cbmc/results.txt`).
- `cbmc/mutants.sh`: 12/12 planted bugs caught (`cbmc/mutants.txt`).
- Not done yet: compiled differential test, independent review, WP for unbounded lengths.

## Still unverified in ex_docmd.c
Everything else in the file (209 of 214 inventory functions), including
`parse_command_modifiers`, `parse_cmd_address`, `parse_count`, `skip_range`, `modifier_len`,
`one_letter_cmd`, `parse_bang`, `skip_cmd_arg`, `find_ex_command`.
