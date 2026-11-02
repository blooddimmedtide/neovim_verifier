---
entry: neovim/src/nvim/regexp.c (8 small helpers)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-legcap; same text as upstream)
toolchain: CBMC 6.4.1
container: ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac (CI)
strength: candidate   # becomes full-correctness after the owner signs off the spec and the review is done
platform: x86_64; CBMC runs with signed and unsigned char
---

# Claim card: Neovim regexp.c small helpers

8 of the 176 functions in regexp.c. With the 3 number readers (`../CLAIM.md`), 11 have a
proof; the rest are open (see `../../regexp_search/PLAN.md`).

## What is proved, for every input in the stated domain

The specs (`harness.c`) come from regexp.c's comments, `:help pattern` and the callers:
a magic character is `c - 256` for a byte `c`, plain characters are `>= 0`.

| Function | Property |
|---|---|
| `no_Magic(x)` | a magic char gives its byte; a plain char (any `x >= 0`) is unchanged |
| `toggle_Magic(x)` | magic char -> its byte; plain char (any `x >= 0`) -> `x - 256` |
| `re_multi_type(c)` | 1 for magic `@ = ?`, 2 for magic `* + {`, 0 for every other `int` |
| `backslash_trans(c)` | `r t e b` -> 13, 9, 27, 8; every other `int` unchanged |
| `re_multiline(prog)` | non-zero exactly when flag 4 ("can match a NL") is set; `*prog` unchanged |
| `vim_regcomp_had_eol()` | returns `had_eol`, unchanged |
| `re_num_cmp(val, scan)` | with `n` the big-endian number in `scan[3..6]`: `scan[7]` `>` gives `val > n`, `<` gives `val < n`, else `val == n`; reads only the node's 8 bytes |
| `nfa_re_num_cmp(val, op, pos)` | op 1: `pos > val`; op 2: `pos < val`; else `pos == val`; any values |

Domain notes: the magic helpers are only called with plain characters (`>= 0`) or magic
characters (`Magic(c)` of a byte); negative values outside that encoding never occur.

## What the proof relies on

1. CBMC 6.4.1 is sound for this code (no loops).
2. Extraction: `build.py` copies the exact text of the 8 functions, sha256 pinned; the prelude
   repeats the macros, `struct regprog` and `had_eol`, each line checked to exist upstream.
   `regengine_T` is opaque (never dereferenced).
3. CBMC checks bounds, pointers, signed overflow, shifts and lossy conversions.

## Evidence

| Check | Command | Result |
|---|---|---|
| CBMC | `bash regexp/leaves/run_cbmc.sh <checkout>` | 16/16 (8 functions x 2 char signednesses), upstream and fixed |
| Planted bugs | `bash regexp/leaves/run_mutants.sh <checkout>` | 20/20 killed |

Still to do before `verified`: independent review, owner sign-off.
