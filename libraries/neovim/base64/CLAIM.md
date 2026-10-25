---
entry: neovim/src/nvim/base64.c
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch fix-base64-decode-over-2gib, commit 7a5d1f164dcdc390a18ccaf231396dc73a2d95d3)
toolchain: nixpkgs-26.11pre1097770.5adc50831c25 (narHash sha256-hVMDyAXU0kxRuG3GygbZkzf5x+aBNEC0NYEJ6KwHtD4=), CBMC 6.4.1 .deb, z3-solver 5.3.1.0
container: ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac (CI)
strength: candidate   # becomes full-correctness only after both reviews sign off
tools: Frama-C 33.0 WP (Typed+Cast, -wp-rte), Why3 1.8.2, Z3, CVC5, CBMC 6.4.1, z3-solver (Python)
platform: x86_64 (gcc/clang data model, signed char, little-endian)
---

# Claim card: Neovim base64.c

## What is proved, for every input

| Function | Property | How |
|---|---|---|
| `base64_encode` | Returns a buffer of `4*ceil(n/3)+1` bytes holding the RFC 4648 Base64 of the input (standard alphabet, `=` padding), NUL-terminated. No runtime errors. Allocates exactly one buffer, which it returns. | Frama-C WP, all goals |
| `base64_decode` (fixed fork) | Returns non-NULL exactly when the input is canonical padded Base64 (length a multiple of 4, alphabet characters, then 0 to 2 `=`, unused low bits zero). On success the length is `n/4*3 - padding` and every byte is the RFC 4648 decoding. On failure `*out_lenp = 0`. No runtime errors. No leak, no double free, never returns freed memory. | Frama-C WP, all goals |
| `base64_decode` (upstream) | The same, for inputs below 2 GiB. At 2 GiB and above it is wrong (see Finding). | Frama-C WP, all goals, with `requires src_len <= 0x7fffffff` |
| `vim_htobe64`, `vim_htobe32` | Result equals the big-endian reading of the input bytes, for every input. Memory safe, terminates. | CBMC, no loops, every input |

The spec is written independently of the code: the RFC alphabet and its inverse are
written out in ACSL (`rfc_char`, `rfc_index`), not taken from the code's tables, and
the proof shows the code's tables equal them.

## Finding

Upstream `base64_decode` keeps the index of the first `=` in an `int`. From 2^31
bytes on, that index wraps negative, the padding check is skipped, invalid input is
accepted, and the returned buffer ends in bytes that were never written. Details and
a reproducer: `../findings/base64-decode-over-2gib.md`. The fix (`size_t`, `SIZE_MAX`
as "none") is proved with no size limit.

## What the proof relies on

1. **Tools are sound.** Frama-C 33 WP has a known bug: it assumes a `const char`
   array initialized from a string literal is all zeros
   (`verification-notes/toolchain-bugs/framac33-wp-string-init.md`). The proved files
   contain no such array: the tool patch `alphabet` rewrites it as a brace list.
2. **Tool patches** (`wp/tool_patches.py`): 5 rewrites that let WP read the code
   (memcpy + htobe64 loads, a `char` vs `uint8_t` read, the alphabet initializer).
   Each is proved identical to the original by a CBMC harness with no assumptions,
   under both byte-order implementations base64.c can be built with (`equiv/`).
3. **Bit lemmas** (`wp/lemmas.py`) are proved with Z3 bit-vectors, not by WP. The
   ACSL text and the Z3 check come from the same strings.
4. **Stub contracts** (`wp/stubs/nvim/memory.h`): `xmalloc` never returns NULL
   (true: Neovim exits on out-of-memory) and returns memory separate from other
   objects. WP ignores allocation state, so ghost variables track it: a live count
   and the last allocation, with `xfree` allowed only on that pointer, once.
5. **C implementation:** x86_64, `char` signed 8-bit, `(char)` of an int keeps the
   low 8 bits (gcc and clang). Other targets are not yet proved.
6. **Encoder input size** at most 4 EiB (2^62 bytes), larger than any x86_64
   address space.
7. **Entry contracts:** `src` is non-NULL and readable for `src_len` bytes, and
   for the decoder `out_lenp` is valid and separate from `src`. This matches
   `FUNC_ATTR_NONNULL_ALL` and the functions' own `assert`s. The proof is run
   with asserts enabled (no `-DNDEBUG`), as in Neovim's default build, so the
   asserts are proved never to fire.
8. **WP's memory model** (Typed+Cast): objects of different C types do not
   alias, pointer casts between `char *` and `uint8_t *` keep the address
   (WP warns "Keep pointer value"; the char/uint8 reads that matter are moved
   to one type by tool patches), and the `xmalloc` result is separate from all
   existing objects (its `\fresh` is not checked by WP; true for malloc).
9. **Upstream decoder** only: `src_len <= 2^31 - 1` (the bug).

## Not covered

- Writing to the buffer after it is freed, without returning it: the ghost tracking
  catches leaks, double frees and returning a freed buffer, but not a stray write
  after `xfree` on the error path (the code does none; the error path only sets
  `*out_lenp = 0` and returns NULL).
- Targets other than x86_64. A trial on Frama-C's ppc_32 machine (32-bit, big-endian,
  unsigned `char`) leaves 6 of 116 fixed-decoder goals unproved, so other targets need
  their own proof work.
- Owner sign-off on the spec (Yerin) is still open.

## Evidence

| Check | Command | Result |
|---|---|---|
| Bit lemmas | `python3 -I wp/lemmas.py` | 44 / 44 proved |
| Tool patch equivalence | `bash equiv/run_equiv.sh <nvim>` | 10 / 10 proved (5 patches x 2 builds) |
| WP encoder | `bash wp/run_wp.sh <nvim>` | 260 / 260 goals, from clean |
| WP decoder (upstream) | `bash wp/run_wp.sh <nvim>` | 120 / 120 goals, from clean |
| WP decoder (fixed) | `bash wp/run_wp.sh <verified_neovim>` | 118 / 118 goals, from clean |
| htobe bridge | `bash bridge/run_bridge.sh <nvim>` | proved |
| Differential test | `python3 -I difftest/difftest.py <nvim>` | 79,534 cases x 3 builds, 0 mismatches (fixed fork: 19,908, 0) |
| Planted bugs | `python3 -I run_mutants.py <nvim> <fixed> --timeout 120` | 35 / 35 caught (`mutants_result.tsv`): 30 by WP goals that pass on the real code, 2 by the tool-patch equivalence harnesses, 3 because they change text a tool patch pins (annotate.py refuses) |
| Independent review | `REVIEW.md` | 2 blocking spec gaps found and fixed; of the 4 gap probes, 3 are now caught by WP and the url-safe alphabet probe is caught only because the alphabet tool patch pins the exact RFC text. Fresh re-review: REVIEW2.md |
| CI, pinned container, twice from clean | `.github/workflows/verify.yml` | passed: [run 40129216377](https://github.com/blooddimmedtide/neovim_verifier/actions/runs/40129216377) and [run 40140031727](https://github.com/blooddimmedtide/neovim_verifier/actions/runs/40140031727), commit f18ed86 |
| Owner review | Yerin | pending |
