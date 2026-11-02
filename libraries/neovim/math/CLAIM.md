---
entry: neovim/src/nvim/math.c
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
toolchain: CBMC 6.4.1 (.deb, see tools/install.sh)
container: ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac (CI)
strength: candidate   # becomes full-correctness after the reviews and the owner's spec sign-off
tools: CBMC 6.4.1 (bit-precise, IEEE 754 doubles, loops fully unwound)
platform: x86_64; both the GCC/Clang build (compiler builtins) and the portable fallback loops
---

# Claim card: Neovim src/nvim/math.c

| Function | Property, for every input |
|---|---|
| `xfpclassify(d)` | the IEEE 754 class of `d` (NaN, infinite, zero, normal, subnormal), compared with CBMC's own float classification, not with a bit test |
| `xisinf(d)`, `xisnan(d)` | true exactly for infinities / NaNs |
| `xctz(x)` | 64 for 0; else the index of the lowest set bit |
| `xpopcount(x)` | the number of set bits |
| `vim_append_digit_int(&v, d)` | for `v >= 0` and `0 <= d <= 9`: `OK` and `v = 10 v + d` when that fits in an `int`; otherwise `FAIL` with `v` unchanged |
| `trim_to_int(x)` | `x` clamped to `[INT_MIN, INT_MAX]` |

## What the proof relies on

1. CBMC is sound for this code (bit-precise integers, IEEE 754 binary64).
2. Extraction: exact upstream text of each function (sha256 pinned, `tools/extract_c.py`) after a
   prelude with math.c's own system headers, Neovim's `OK` (1) and `FAIL` (0), checked against
   `vim_defs.h`, and `FUNC_ATTR_CONST` as nothing.
3. Precondition of `vim_append_digit_int`: `v >= 0`, `0 <= d <= 9`. Its only caller
   (`normal.c`, `z{count}`) starts from a digit and only appends digits or divides by 10.
   For negative `v` the function can overflow (`x * 10` with `x < INT_MIN / 10`); no caller does that.
4. `xpopcount` on NetBSD calls the system's `popcount64`, which is not covered.

## Evidence

| Check | Command | Result |
|---|---|---|
| CBMC | `bash cbmc/run_cbmc.sh <nvim>` | 5 / 5 harnesses, builtin and fallback builds |
| Planted bugs (own, not the reviewer's) | see thread notes | 5 / 5 caught |
| Independent review, reviewer's planted bugs | | pending |
| Owner review | Yerin | pending |
