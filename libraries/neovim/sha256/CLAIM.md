---
entry: neovim/src/nvim/sha256.c (all 6 functions)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: blooddimmedtide/verified_neovim branch fix-sha256-over-8gib (PR #4)
toolchain: CBMC 6.4.1 (goto-cc, goto-instrument --dfcc), Python 3 for the structure check
container: ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac (CI)
strength: candidate   # becomes full-correctness after the review and the owner's spec sign-off
tools: CBMC bounded model checking (no bound is left: every loop is either fully unrolled with
  unwinding assertions or replaced by a proved loop contract), DFCC loop contracts
platform: x86_64 (size_t 64-bit, uint32_t, gcc/clang)
---

# Claim card: Neovim sha256.c

The C file is compiled unchanged (the proofs `#include` it). The only edit is in
`cbmc/build.py`, used for `sha256_update`: it inserts a CBMC loop contract in front of the
`while` loop's body and checks that removing it gives back the upstream text.

## What is proved, for every input

The spec is FIPS 180-4 section 6.2, written out in `cbmc/spec.h` (functions Ch, Maj, Σ0, Σ1,
σ0, σ1, the 64 constants K and the initial hash H(0), and the compression function).

| Function | Property | How |
|---|---|---|
| `sha256_start` | sets the state to H(0) and the length to 0 | `h_start` |
| `sha256_process` (static) | one FIPS compression of the state with the 64-byte block, for every state and block | composition, below |
| `sha256_update(ctx, in, len)` | with `left` bytes already buffered: hands `sha256_process` exactly the next whole 64-byte blocks of the stream (buffer + input), in order, with the caller's context; keeps the remaining bytes buffered in place; adds `len` to the 64-bit byte count | `h_update` (loop contract) |
| `sha256_finish` | feeds the FIPS padding (0x80, zeros, 64-bit big-endian bit length) as the remaining blocks, then writes the state big-endian as the 32-byte digest | `h_finish` |
| `sha256_bytes(buf, n, salt, m)` | returns the lowercase hex of SHA-256(buf ‖ salt) (salt omitted when NULL), 64 characters and a NUL | `h_bytes` |
| `sha256_self_test` | returns true; no undefined behavior | native run, below |

On upstream, `sha256_update`'s property needs each call's `len` below 4 GiB, so
`sha256_bytes` is correct upstream when `buf_len` and `salt_len` are below 4 GiB. On the fixed
fork both hold for every length.

All harnesses: `--bounds-check --pointer-check --signed-overflow-check --undefined-shift-check`
and `--unwinding-assertions`, so no out-of-bounds access, no signed overflow, no undefined
shift and no unproved bound. (`--pointer-overflow-check` and `--pointer-primitive-check` are
not used.)

### How `sha256_process` is proved

Checking the whole compression in one CBMC query does not finish (over 10 minutes for one
SAT problem of 64 rounds). It is proved in parts instead:

1. `h_prims`: the macros S0, S1, S2, S3, F0, F1 equal σ0, σ1, Σ0, Σ1, Maj, Ch for all inputs.
2. `h_forms`: the alternative Ch/Maj forms are equal to FIPS's (used by `spec.h`).
3. `h_round`: one `P(a, b, c, d, e, f, g, h, x, K)` sets `d += T1` and `h = T1 + T2` and
   leaves the other six unchanged, which is a FIPS round with the names rotated by one.
4. `h_sched`: `R(t)` computes FIPS's W[t] from earlier words and writes only W[t], for every
   t in 16..63.
5. `h_endian`: GET_UINT32 / PUT_UINT32 are big-endian loads and stores of 4 bytes.
6. `check_structure.py` reads the function body and checks every statement in order: 16
   GET_UINT32 loads, A..H loaded from the state, 64 `P` calls with the names rotated right
   by t, the message word W[t] or R(t), and FIPS's K[t] (from `spec.h`), then
   `state[i] += A..H`, 98 statements and nothing else. It works like the C preprocessor's
   first phases (joins backslash-continued lines, then removes comments) and also checks:
   every directive in the file is one of the 8 expected `#include`s or one of 13 `#define`s,
   each macro defined exactly once (no `#undef`, no `#if`), so the macros proved in steps
   1-5 are the ones the body uses; the 10 macros in the body are exactly the expected ones;
   nothing sits between `sha256_process` and `sha256_update`; and none of the Neovim headers
   it includes (12, followed transitively) defines a macro named like anything in the body,
   except `SHA256_BUFFER_SIZE`, which must be `64`.

Steps 1-5 are machine proofs. Step 6 is a short script, and the step from "names rotated
right by t" to FIPS's "h = g; ...; a = T1 + T2" is a paper argument (one rotation per round
is the same renaming); both are in the trusted list below. Planted bugs in the K table, the
rotations, the schedule, the argument order and the macros are caught, including a macro
redefined after the function and a comment that hides a statement (review B1).

### How the stream functions are proved

`sha256_update`, `sha256_finish` and `sha256_bytes` are proved with the next function down
replaced by a recorder (`goto-instrument --replace-calls`). The recorder checks, at an
arbitrary byte index chosen by CBMC, that each call gets exactly the bytes and arguments the
spec says. Because the index is arbitrary, a passing proof covers every byte. The recorders
also keep a shadow copy of what the callee left: `rec_process` gives the state an arbitrary
new value, records it, and checks on the next call (and at the end) that the state is
exactly that value; in `h_bytes` each recorder gives the whole context arbitrary contents and
the next one checks it is unchanged. So no code between two compressions may touch the hash
state (review B2). With the `sha256_process` proof this gives SHA-256 of the whole input.

- `sha256_update` has an unbounded loop. Its loop contract (`LOOP_INV` in
  `harness_stream.c`) states how many blocks have been processed and where `input` and
  `length` are, and that the state is what the last compression left. CBMC proves the invariant holds at entry, is kept by each iteration, and the
  `decreases` clause shows the loop ends. So the proof covers every `len`, not a bound.
- `sha256_finish` calls the real `sha256_update` twice (padding, then length).
- `sha256_bytes`'s calls to `snprintf("%02x")` go to a fixed-arity model (CBMC does not
  support variadic functions). The model checks that the format is exactly `"%02x"` and the
  value is a byte, then writes the two digits.

### sha256_self_test

It has no inputs: its only state is two static flags. The differential test runs it natively
under ASan and UBSan, first call and second (cached) call, and it returns true. Since the hash
is proved correct above, the "failures" branch is dead. In `h_bytes` it is replaced by a
recorder, because its result does not change what `sha256_bytes` returns.

## Upstream bug found

`sha256_update` adds only the low 32 bits of `length` and adds at most 1 to the high word, so
the high bits of the length are dropped: one call with 8 GiB or more (or 4 GiB or more when
the low word also carries) gives a wrong digest. See `../findings/sha256-length-over-8gib.md`. The proof of upstream assumes `len <= 0xFFFFFFFF`
per call; with `-DSHA256_FIXED` (the fork's fix, PR #4) that assumption is removed and the
proof covers every `size_t` length.

## What the proof relies on

1. **CBMC 6.4.1 is sound**, including DFCC loop contracts.
2. **`check_structure.py`** reads the source correctly (about 150 lines; the review's mutants
   in the body, a late redefinition and a comment splice are caught), and system headers
   (`<stdio.h>` and the others) define none of the body's names.
3. **The rotation argument** in "How `sha256_process` is proved" (paper, checked by the
   reviewer).
4. **The `snprintf` model** matches glibc for `"%02x"` on a byte value with room for 3 chars.
5. **`memcpy`, `memset`, `memcmp`, `strlen`** behave as C11 says (CBMC's built-in models).
6. **Preconditions**: `ctx` is a context started by `sha256_start` and only changed by these
   functions; `input` valid for `len` bytes; `left0 + len` does not wrap a `size_t` (an
   object can't be that large).
7. `sha256_self_test` is covered by one native run, not a proof (it has no inputs).
8. **CBMC's pointer model** keeps object offsets in 56 bits by default, so "every `size_t`
   length" on the fork means every length below 2^56 bytes. x86_64 objects are below 2^47
   bytes, so no real input is left out.

## Not covered

- Owner sign-off on the spec (Yerin).

## Evidence

| Check | Command | Result |
|---|---|---|
| Compression pieces | `bash cbmc/run_cbmc.sh <nvim>` | h_forms, h_start, h_prims, h_round, h_sched, h_endian proved (43 s) |
| Compression structure | `python3 -I cbmc/check_structure.py <nvim>` | 98 statements match FIPS 180-4; 13 macros each defined once, no other directives; 12 Neovim headers clean |
| update, upstream (each call < 4 GiB) | `bash cbmc/run_stream.sh <nvim>` | proved (about 25 min) |
| update, fixed fork (every len) | `bash cbmc/run_stream.sh <fork> fixed` | proved |
| finish | `bash cbmc/run_finish.sh <nvim>` | proved (3 min with the state shadow) |
| bytes | `bash cbmc/run_bytes.sh <nvim>` | proved |
| Differential test (gcc -O2, ASan/UBSan, vs Python hashlib) | `python3 -I difftest/difftest.py <nvim> 20000` | self-test passed; 40,000 digests, 0 mismatches (sha256_bytes checked against the exact salted or unsalted hash) |
| Independent review | `REVIEW.md` | accept with changes; both blocking issues (B1, B2) fixed, see "Changes after the review" there |
| Planted bugs | `python3 -I run_mutants.py <nvim>` (`mutants.toml`) | 30 chosen by the reviewer: 29 caught by the proofs after the fixes, the self-test-vector one by the native run (as stated above) |
| CI, pinned container, twice | `.github/workflows/verify.yml` | pending |
| Owner review | Yerin | pending |
