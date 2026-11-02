---
entry: neovim/src/nvim/search.c (set_last_csearch)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-legcap, commit 01c749d)
toolchain: CBMC 6.4.1
container: ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac (CI)
strength: candidate   # becomes full-correctness after the owner signs off the spec and the review is done
platform: x86_64; CBMC runs with signed and unsigned char
---

# Claim card: Neovim search.c set_last_csearch

`set_last_csearch(c, s, len)` stores the character that `;` and `,` repeat (set by
`setcharsearch()`). It is 1 of the 57 functions in search.c; the rest of the file is open
(see `../regexp_search/PLAN.md`).

## What is proved, for every input (fixed fork)

Precondition: `len >= 0` and `s` points to at least `len` readable bytes. The only caller
(`setcharsearch()`, eval/funcs.c) passes `utfc_ptr2len(s)` of a NUL-terminated string, which
meets it. With `n` the value of `lastc_bytelen` afterwards:

1. `lastc[0] == (uint8_t)c`, `lastc[1]` unchanged;
2. `len <= 32`: `n == len`. `len > 32`: `n` is the largest `k` in 1..32 with `s[k]` not a
   UTF-8 trail byte, or 0 if there is none, so the cut keeps only whole characters;
3. `lastc_bytes[0..n) == s[0..n)` and `lastc_bytes[n..32]` are NUL (from any earlier contents);
4. no out-of-bounds access, signed overflow or other undefined behaviour.

`len` ranges over every non-negative `int` (the function reads at most `s[0..32]`). The spec
is written in `cbmc/harness.c` from the doc of `getcharsearch()` (a NUL-terminated character)
and the fix's rule (whole characters, at most `MAX_SCHAR_SIZE` bytes), not from the code.

## Finding

Upstream copies `len` bytes into the 33-byte `lastc_bytes`: `setcharsearch()` with a character
that has many composing characters writes past it, and bytes of a longer earlier character are
left after a shorter one. On upstream the same harness fails with the out-of-bounds write and
the "tail cleared" property. Details: `../findings/search-csearch-overflow.md`.

## What the proof relies on

1. CBMC 6.4.1 is sound for this code (bounded loops, all unwound with `--unwinding-assertions`).
2. Extraction: `cbmc/build.py` copies the exact text of `set_last_csearch` (search.c) and
   `utf_is_trail_byte` (mbyte.h), sha256 pinned. The prelude repeats `MAX_SCHAR_SIZE`,
   `CLEAR_FIELD` and the three globals; each line is checked to exist upstream.
3. `memset`/`memcpy` are CBMC's models of the C library functions.

## Evidence

| Check | Command | Result |
|---|---|---|
| CBMC, fixed | `bash search/cbmc/run_cbmc.sh <fixed>` | proved, 2 char signednesses x 2 length ranges |
| CBMC, upstream | `bash search/cbmc/run_cbmc.sh <upstream>` | refuted as expected (overflow + stale bytes) |
| Planted bugs | `bash search/cbmc/run_mutants.sh <fixed>` | 9/9 killed |
| Neovim tests | `test_charsearch.vim`, `test_search.vim`, `test_normal.vim` on the fixed fork (ASan) | pass (test_normal's Test_normal25_tag needs help tags, absent in this build) |

Still to do before `verified`: independent review, owner sign-off.
