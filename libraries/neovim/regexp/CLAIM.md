---
entry: neovim/src/nvim/regexp.c (pattern number readers)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-legcap, commit 3336e2d)
toolchain: Frama-C 33 WP with Z3 and CVC5 (tools/install.sh), CBMC 6.4.1, gcc for the differential test
container: ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac (CI)
strength: candidate   # becomes full-correctness after the owner signs off the spec and the review is done
platform: x86_64; CBMC and the differential test run with signed and unsigned char
---

# Claim card: Neovim regexp.c number readers

These three static helpers read the numbers in `\%d123`, `\%o40`, `\%x2a`, `\%u20AC`,
`\%U1234abcd`, `\@123<=` and `[\d123]`. They are 3 of the 176 functions in regexp.c; the
rest of the file is open (see `../regexp_search/PLAN.md`).

## What is proved, for every input

| Function | Tool | Property |
|---|---|---|
| `getdecchrs()` (fixed fork) | Frama-C WP, 41/41 goals | When `regparse` starts with k decimal digits followed by a non-digit: k = 0 gives -1 and changes nothing; k > 0 moves `regparse` by exactly k, sets `curchr` to -1 and returns the digits' value, or `INT_MAX + 1` when the value is above `INT_MAX`. Any k |
| `getdecchrs()` (upstream) | Frama-C WP, 43/43 goals | The same with the exact value, only for k <= `INT_MAX` and value <= `INT64_MAX`; beyond that it overflows (see Finding) |
| `gethexchrs(max)`, max in {2, 4, 8} (the callers' values) | CBMC | -1 and no move when the first byte is not a hex digit; else reads the longest run of at most max hex digits (0-9, a-f, A-F), returns its value and moves past it. Reads only `regparse[0 .. max-1]` |
| `getoctchrs()` | CBMC | -1 and no move when the first byte is not an octal digit; else reads the longest run of at most 3 octal digits whose value is at most 0377 ("400" reads as 040), returns its value and moves past it. Reads only `regparse[0 .. 2]` |

The references are the positional values of the digit strings (`wp/contracts.py` `dval`,
`cbmc/spec.h`), written from the digit definitions and the doc comments, not from the code.
What the references decide themselves: the -1 for "no digit" and `INT_MAX + 1` for "too
large" (both from the doc comment and the fix), and the octal stop rule (from the doc comment
"400 is treated as 40").

## Finding

`getdecchrs` overflows `int64_t` on 19 or more digits and its `int` counter on 2^31 digits
(undefined behavior; wrapped values make `\%d18446744073709551681` match `A`). Details:
`../findings/regexp-getdecchrs-overflow.md`. Fixed in the fork and proved for every input.

## What the proof relies on

1. Frama-C WP 33 (Typed+Cast model), Z3 and CVC5 are sound for this code (no string literals,
   so the known Frama-C 33 string-literal bug does not apply). CBMC 6.4.1 is sound.
2. Extraction: `wp/build.py` and `cbmc/build.py` copy the exact text of each function
   (sha256 pinned); the WP copy only adds ACSL comments and a ghost parameter `k` (the digit
   run length), checked by stripping them. The prelude declares `regparse` and `curchr` as
   regexp.c does; `hex2nr` (charset.c) and `ascii_isxdigit` (ascii_defs.h) are included
   verbatim as callees of the CBMC proofs.
3. Preconditions, each documented or forced by the callers: `gethexchrs` gets max = 2, 4 or 8
   (all its call sites); `regparse` points at readable memory up to the first non-digit (true
   for every caller: patterns are NUL-terminated strings). `dval_mono` is a ghost lemma
   function proved by WP (monotonicity of the value along a digit run).
4. WP's `-wp-rte` covers signed overflow, invalid memory access and the ghost code; CBMC runs
   with bounds, pointer, signed-overflow and shift checks, all loops fully unwound.

## Evidence

| Check | Command | Result |
|---|---|---|
| WP, upstream | `bash regexp/wp/run_wp.sh <upstream>` | dval_mono 15/15, getdecchrs 43/43 |
| WP, fixed | `bash regexp/wp/run_wp.sh <fixed>` | dval_mono 15/15, getdecchrs 41/41 |
| CBMC | `bash regexp/cbmc/run_cbmc.sh <checkout>` | 4/4 harnesses (2 functions x 2 char signednesses), upstream and fixed |
| Differential | `bash regexp/difftest/run_difftest.sh <checkout>` | 279,620 (upstream) / 351,505 (fixed, with getdecchrs) checks per signedness, 0 mismatches |

Still to do before `verified`: independent review with planted bugs, owner sign-off.
