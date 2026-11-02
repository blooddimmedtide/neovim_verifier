---
entry: neovim/src/nvim/memory.c (15 string and byte-buffer helpers)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: none needed (no bug found)
toolchain: Frama-C 33.0 WP, Why3, Z3 5.1.0, CVC5 1.4.0 with --full-saturate-quant (tools/install.sh, tools/bin/cvc5-fsq)
container: ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac (CI)
strength: candidate   # becomes full-correctness after the review and the owner's spec sign-off
tools: Frama-C WP (deductive, unbounded: every length, every input), Typed+Cast memory model, -wp-rte
platform: x86_64 (machdep x86_64); results hold for signed and unsigned char (differential test runs both)
---

# Claim card: Neovim memory.c string helpers

`wp/build.py` copies the exact upstream text of each function (sha256 pinned) and adds ACSL
as comments only: contracts, loop invariants, assertions, ghost statements and, for four
functions, a ghost parameter naming the length of a string argument. The build checks that
removing the comments gives back the upstream text. Nothing is admitted; no axioms; the only
`assumes` are behavior clauses whose completeness and disjointness are proved.

## What is proved, for every input

"String of length n" = n readable non-NUL bytes followed by a readable NUL (`str_len`).
Values in results refer to the memory before the call.

| Function | Property |
|---|---|
| `xmemcpyz(dst, src, len)` | copies `src[0..len-1]` to `dst`, writes `dst[len] = NUL`, returns `dst`; writes nothing else |
| `xstrnlen(s, n)` | the index of the first NUL among `s[0..n-1]`, else `n`; reads nothing after the first NUL |
| `xstrchrnul(str, c)` | pointer to the first byte equal to `c` or NUL |
| `xmemscan(addr, c, size)` | pointer to the first `c` in `addr[0..size-1]`, else `addr + size`; reads nothing past the first match |
| `strchrsub(str, c, x)` (c != NUL) | every `c` in the string becomes `x`, every other byte (and the NUL) is unchanged; writes only `str[0..n]` |
| `memchrsub(data, c, x, len)` | every `c` in `data[0..len-1]` becomes `x`, others unchanged; writes only those bytes |
| `strcnt(str, c)` (c != NUL) | the number of `c` bytes in the string |
| `memcnt(data, c, len)` | the number of `c` bytes in `data[0..len-1]` |
| `xstpcpy(dst, src)` | copies the string with its NUL, returns `dst + n` |
| `xstpncpy(dst, src, maxlen)` | copies `src` up to its NUL or `maxlen` bytes, fills the rest of `dst[0..maxlen-1]` with NUL, returns a pointer to the first NUL written, else `dst + maxlen`; reads nothing after the first NUL |
| `xstrlcpy(dst, src, dsize)` | returns the length of `src`; if `dsize > 0`, `dst` holds the first `min(n, dsize-1)` bytes and a NUL; writes only `dst[0..dsize-1]` |
| `xstrlcat(dst, src, dsize)` | with `dst` a string of length `m < dsize`: returns `m + n`, keeps `dst[0..m-1]`, appends the first `min(n, dsize-m-1)` bytes of `src` and a NUL |
| `xmemrchr(src, c, len)` | pointer to the last byte equal to `c` in `src[0..len-1]`, or NULL |
| `strequal(a, b)` | true iff both are NULL, or both are strings with the same bytes |
| `strnequal(a, b, n)` | true iff both are NULL, or both are non-NULL and agree on the first `n` bytes up to and including a NUL |

All functions: no undefined behavior (`-wp-rte`: every memory access valid, no signed
overflow, no invalid conversion), and they terminate (loop variants).

## What the proof relies on

1. **Frama-C WP, Why3 and the provers are sound** (Z3, CVC5).
2. **The C library meets `wp/stubs/vp_string.h`**: contracts for strlen, memchr, strchr,
   memcpy, memmove, memset, strcmp, strncmp written from C11 7.24, with no axioms. memchr and
   strchr are specified to read in order and stop at the first match (true of glibc and C11's
   description). Frama-C's own libc header was not used: its memchr compares a signed char
   with an int (wrong above 127).
3. **Preconditions** (each function's `requires`): pointers valid for the bytes the doc
   comments say are used; `c != NUL` for `strchrsub` and `strcnt` (their own `assert`s);
   `xstrlcat`: `dsize > 0` and the existing string shorter than `dsize` (its own `assert`s);
   no overlap where the code uses `memcpy` (`xmemcpyz`, `xstpcpy`, `xstpncpy`, `xstrlcpy`).
4. **No C object is larger than `PTRDIFF_MAX`** (`xstpcpy`, `xstrlcat`): rules out a string of
   `SIZE_MAX` bytes, where `len + 1` would wrap. True on every x86_64 system.
5. **Ghost length parameters** (`strchrsub`, `strcnt`, `xstpcpy`, `xstrlcat`): the contract
   names the string length `n` (a string has exactly one, `lemma str_len_unique`, proved),
   so "for every string" is "for every n with `str_len(s, n)`". This is notation, not an
   assumption: callers do not pass anything.

## Not covered

- The rest of memory.c (allocation wrappers, `xstrdup`, `arena_*`, ...). Those depend on
  malloc and on `preserve_exit`, and need a separate model.
- Owner sign-off on the spec (Yerin). Independent review and planted bugs: pending.

## Evidence

| Check | Command | Result |
|---|---|---|
| WP, upstream | `bash wp/run_wp.sh <nvim> 60` | every goal proved: 15 functions, 2 ghost lemma functions, 2 lemmas (333 goals) |
| Differential test (gcc -O2, glibc, ASan/UBSan, signed and unsigned char) | `bash difftest/run_difftest.sh <nvim> 3000000` | 45,000,000 checks each, 0 mismatches |
| Independent review | | pending |
| Planted bugs | | pending (reviewer's choice) |
| CI, pinned container, twice | `.github/workflows/verify.yml` | pending |
| Owner review | Yerin | pending |
