---
entry: neovim/src/nvim/mbyte.c (UTF-8 byte helpers)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch fix-cp-bounds-over-2gib, commit aec5ed2; all fixes together: branch verified, 053a6f2)
toolchain: CBMC 6.4.1 (.deb, see tools/install.sh), gcc for the differential test
container: ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac (CI)
strength: candidate   # becomes full-correctness after the owner signs off the spec
tools: CBMC 6.4.1 (bit-precise bounded model checking; every loop fully unwound, proved by unwinding assertions)
platform: x86_64, char signed (Neovim's build) and unsigned (both proved)
---

# Claim card: Neovim mbyte.c UTF-8 byte helpers

## What is proved, for every input

"UTF-8" here means the original 1 to 6 byte form (RFC 2279), which Neovim deliberately
accepts: values up to 0x7FFFFFFF, overlong forms and surrogates are decoded and encoded
like any other value. It is not a check for valid RFC 3629 UTF-8.

| Function | Property |
|---|---|
| `utf_byte2len(b)`, 0 <= b <= 255 | the length the lead byte announces (its count of leading 1 bits; 1 for a continuation byte, 0xFE and 0xFF) |
| `utf_char2len(c)` | for c >= 0, the length of the shortest encoding of c; for c < 0, 1 |
| `utf_char2bytes(c, buf)` | for c >= 0, writes the shortest well-formed encoding of c (right lead byte, continuation bytes, decodes back to c) and returns its length; for c < 0, writes the low 8 bits of c as one byte and returns 1. Writes `buf[0..r-1]` and nothing else |
| `utf_ptr2len(p)` | 0 for "", the announced length when all its continuation bytes follow, else 1. Reads nothing past the NUL |
| `utf_ptr2char(p)` | the value of a complete sequence at p, else the first byte's value. Reads nothing past the NUL |
| `utf_ptr2len_len(p, size)` | 1 when the lead byte is a 1-byte sequence (also NUL); else the announced length L when the continuation bytes among the first `size` bytes are all right (so L > size means "cut off"), else 1. Reads `p[0]` always and nothing past `p[max(size,1) - 1]` |
| `utf_cp_bounds_len(base, p, p_len)` (fixed fork) | the offsets to the first byte and one past the last byte of the codepoint containing p, when p is inside a lead byte at most 5 bytes back (not before base) plus its continuation bytes, all within `p_len`; else (0, 1). Reads nothing before base, more than 5 bytes back, or at or past `p + p_len`. Any distance `p - base` |
| `utf_cp_bounds(base, p)` | the same with `p_len = INT_MAX` on a NUL-terminated stream; reads nothing past the NUL (fixed fork: any distance) |
| `utf_cp_bounds_len` (upstream) | the same, for `p - base <= INT_MAX`. Past that it is wrong (see Finding) |

The references (`cbmc/spec.h`) are written from the UTF-8 definition (leading-one counts,
6 value bits per continuation byte, value bits per length), not from Neovim's table or
constants. For bad input they return what the functions document (first byte, or 1, or
(0, 1)); that choice is a stated part of the spec, not derived independently.

## Finding

`utf_cp_bounds_len` converts the distance `p - base` to `int`. From 2^31 bytes on this is
undefined behavior, a wrong result, or an out-of-bounds read before `base`, reachable from
`vim.str_utf_start` / `vim.str_utf_end` with a Lua string over 2 GiB in PUC Lua builds.
Details and reproducer: `../findings/cp-bounds-over-2gib.md`. The fix is proved for every distance.

## What the proof relies on

1. **CBMC is sound** for this code: bit-precise C semantics, x86_64 data model.
2. **Extraction** (`cbmc/extract.py`, `build.py`): the proved file is the exact upstream text
   of each piece (sha256 pinned) after a prelude. The prelude defines `EXPECT(c, v)` as `(c)`
   (Neovim: `__builtin_expect`, same value), `FUNC_ATTR_*` as nothing (attributes only), and
   `NUL`, `MIN`, `MB_MAXCHAR` as in Neovim's headers (checked against the header text).
3. **Implementation-defined conversions:** converting an out-of-range value to `char` keeps
   the low 8 bits (GCC, Clang, MSVC).
4. **Preconditions** (the harnesses' `__CPROVER_assume`s, all input domains):
   `0 <= b <= 255` for `utf_byte2len` (documented); pointers non-NULL; strings NUL-terminated;
   `p[0]` readable for `utf_ptr2len_len`; `p_len > 0` and `base <= p` for `utf_cp_bounds_len`
   (its own `assert`); and upstream only, `p - base <= INT_MAX`.
5. **Long inputs:** strings longer than 6 bytes and `size` / `p_len` above 6 are covered by
   giving the function an object of exactly 6 readable bytes: the pointer check proves it never
   reads further, so the result holds for every longer input with the same first bytes.

## Not covered

- The callers in `lua/stdlib.c` (the second half of the fix, a clamp to `INT_MAX`).
- The rest of mbyte.c (composing characters, grapheme clusters, case folding, iconv, ...).
- Owner sign-off on the spec (Yerin).

## Evidence

| Check | Command | Result |
|---|---|---|
| CBMC, upstream | `bash cbmc/run_cbmc.sh <nvim>` | 10 / 10 harnesses, signed and unsigned char |
| CBMC, fixed fork | `bash cbmc/run_cbmc.sh <verified_neovim>` | 10 / 10 harnesses, signed and unsigned char |
| Differential test (gcc -O2 -fsigned-char vs the references) | `bash cbmc/run_difftest.sh <nvim>` | 4,341,614,208 cases, 0 mismatches |
| Independent review | `cbmc/REVIEW.md` | accept with changes; the required claim wording is in this card |
| Planted bugs | `python3 -I cbmc/run_mutants.py <nvim>` | reviewer's 27 for the six helpers: 24 caught, 3 equivalent (REVIEW.md); bounds functions: second review in progress |
| CI, pinned container, twice | `.github/workflows/verify.yml` | pending |
| Owner review | Yerin | pending |
