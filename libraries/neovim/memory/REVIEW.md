# Independent review: Frama-C WP proof of memory.c string helpers

Reviewer: fresh adversarial reviewer (Claude), 2026-11-02. Checkout: upstream 7b87ce8.
Scope: CLAIM.md, wp/build.py, wp/contracts.py, wp/stubs/vp_string.h, wp/run_wp.sh, difftest/.

## Verdict: **accept with changes**

The proof stands. It reproduces (333/333 goals). It is not vacuous: 46 `assert \false`
probes stay unproved. The libc stubs are consistent and match glibc. Every non-equivalent
planted bug is caught. No precondition I found is stronger than what the doc comments or
the real callers guarantee. The required changes are to the wording of CLAIM.md's trusted
base, not to the proof.

## Blocking findings (CLAIM.md wording; the proof needs no change)

**B1. The trusted-base wording overstates the C standard.** CLAIM.md item 2 says memchr and
strchr "read in order and stop at the first match (true of glibc and C11's description)".
- memchr: C11 7.24.5.1 does not promise a sequential read that stops at the first match.
  That guarantee is in POSIX (memchr: "as if they read the memory byte by byte ... and stop
  at the first occurrence") and in C23 7.26.5.2. The stub's `requires` (valid only up to
  the first match) depends on it. `xstrnlen`, `xmemscan`, `xstpncpy` and the claims "reads
  nothing after the first NUL/match" all rest on it.
- strncmp: the stub requires readability only up to the first mismatch or NUL. No C
  standard and no POSIX text promises that strncmp stops at a mismatch. It is true of
  glibc, whose word-wise reads never cross into an unmapped page, but it is an assumption
  about glibc. `strnequal`'s precondition rests on it.

  Fix: say "POSIX / C23 (memchr), glibc behaviour (strncmp's stop at the first mismatch)"
  and list the strncmp assumption explicitly.

**B2. libc termination is assumed, but the trusted base does not say so.** Frama-C prints
"Neither code nor explicit exits and terminates for function strlen, generating default
clauses". The "they terminate" claim therefore assumes that strlen, memchr, strchr,
memcpy, memmove, memset, strcmp and strncmp terminate. Add one line to the trusted base.

## Non-blocking notes

1. **Preconditions vs. callers.** I checked the doc comments and grepped every caller in
   src/nvim:
   - `strchrsub`: 6 callers (path.c, api/buffer.c, eval.c), all with a non-NUL constant
     `c`, so `c != 0` holds. `strcnt` has no callers outside memory.c.
   - `xstrlcat` (57 callers): `dsize > 0 && m < dsize` is exactly the function's own two
     `assert`s, and the doc requires both ("Must be greater than 0", "Must have a NUL
     byte"). Overlap is allowed (memmove, no `\separated`), as the doc says.
   - Separation: a search for calls whose dst and src share an identifier found no
     overlapping call to xmemcpyz, xstpcpy, xstpncpy or xstrlcpy.
   - Three separation requirements are stricter than the code needs, though consistent
     with the docs and with `restrict`:
     - `xmemcpyz` separates `dst[len]` from `src`.
     - `xstrlcpy` separates the whole `dst[0..dsize-1]` from `src[0..n]`. The code only
       needs `dst[0..min(n, dsize-1)]`.
     - `xstpncpy` separates `src[0..maxlen-1]` even when the string is shorter.

     Legal but unusual calls are therefore outside the claim. For example,
     `xstrlcpy(buf, buf + 5, 10)` with a 2-byte string does not satisfy the precondition.
     xstpncpy has no callers at all. Suggest one sentence in CLAIM.md.
   - The PTRDIFF_MAX bounds are fine (no object is larger).
   - `xstrnlen`/`xmemscan` allow `n`/`size` larger than the object as long as the match
     is in bounds. strings.c:1806 depends on that, and the stub permits it (the probe
     `h_memchr_short` stays consistent).

2. **Postconditions vs. CLAIM table.** Each row matches its contract. "Writes nothing else"
   and "reads nothing after the first NUL" are carried by `assigns` and by the
   prefix-validity `requires`, which `-wp-rte` and the stub preconditions enforce.
   - `xstrlcat` does not state that the bytes after the new NUL are unchanged. CLAIM does
     not claim it either.
   - `xmemrchr`'s spec is stated over the `uint8_t *` view. That is the code's own view.

3. **libc stubs vs. C11/glibc.** I read each contract against the standard:
   - strlen, strchr (including `c == 0` returning the NUL and conversion to `char`),
     memcpy (no overlap), memmove, memset, strcmp (`== 0` iff equal strings) and strncmp
     (`== 0` iff equal up to n bytes / the first NUL) are correct.
   - memchr's `byte_is` compares as unsigned char, which is correct. The only issue is
     the "stops at first match" wording (B1).
   - `frama-c -print` shows only the stub contracts. None of Frama-C's own string.h is
     merged in: the only headers included are assert.h, stdbool.h, stdint.h and
     features.h.
   - Consistency: the 16 `assert \false` probes placed after calls to each stub, on
     concrete buffers, all stay unproved. Seven of eight positive sanity asserts are
     proved, e.g. `strlen("abc") == 3`, `strchr(s, 0)` gives the NUL, and strncmp gives
     `n = 1` equal and `n = 2` unequal. See `review/stub_consistency.c`. The eighth is a
     Typed+Cast limitation (an `unsigned char[]` read through `char *`).

4. **The pointer-quantified forms are equivalent to the index forms.** I checked the new
   `str_len` and the memset `ensures`.
   - Pointer to index: proved as lemmas (`review/equiv_lemmas.c`; `str_ptr_to_idx` and
     `set_ptr_to_idx` proved, plus `decomp`).
   - Index to pointer: provers time out as stand-alone lemmas because of instantiation.
     It is proved pointwise for arbitrary `q` (`review/equiv_pointwise.c`, 16/16).
   - So the stub ensures are not stronger than the index forms.
   - `str_len_unique` is proved, so the ghost length parameters are notation.

5. **Ghost code.**
   - Ghost statements write only the ghost locals `g` and `s0`. Frama-C rejects ghost
     writes to non-ghost lvalues.
   - The ghost calls `count_le`/`count_gap` are `assigns \nothing`. Their loops have
     variants, proved in their own runs (9/9 each).
   - No ghost statement can change program behaviour.

6. **Vacuity.** 30 in-function probes are unproved (timeout at 20 s): at entry, on every
   return path and in every loop body of all 15 functions. Entry probes test that the
   requires are satisfiable; path probes test that the stub ensures do not kill the path.
   - Method caveat: WP uses earlier asserts as hypotheses. Entry probes and path probes
     were therefore run in separate passes (`review/probe_entry.py`,
     `review/probe_paths.py ret|body`).
   - The harness block at the end of `probe_entry.py` is superseded by
     `stub_consistency.c`; see 7.

7. **Toolchain finding: WP is unsound on local string-literal array initializers.** For
   `char b[4] = "ab";` WP (Typed and Typed+Cast) produces the hypothesis
   `b[i] == 0 for 0 <= i <= 2`. It then proves `assert b[0] == 0`.
   `char b[4] = {'a','b',0,0}` is handled correctly. Reproducer:
   `review/wp_string_init_bug.c`.
   - It does not affect this proof: no verified function has an array initializer
     (checked on the build output).
   - Recommendation: record it in the toolchain-bug notes, and add a guard to
     run_wp.sh, e.g. reject `= "` initializers in the C part of the build output.

8. **Dangling reference.** vp_string.h cites
   `verification-notes/toolchain-bugs/framac-libc-memchr.md`, which does not exist in the
   repo.

9. **Signed char only.** The proof uses machdep x86_64, so `char` is signed. Unsigned-char
   targets such as aarch64 Linux are covered only by the difftest (`-funsigned-char`).
   CLAIM states the platform, but the phrase "results hold for signed and unsigned char"
   should say the unsigned part is tested, not proved.

10. **What `-wp-rte` checks.**
    - It does not check unsigned wrap (`len + 1`, `dsize - dlen - 1`, `len--`). The
      functional postconditions cover those.
    - It does not check out-of-object pointer arithmetic (`-warn-invalid-pointer` is
      off). None occurs on the specified domain.
    - The CLAIM wording ("no signed overflow") is accurate.

11. **Typed+Cast.** It warns on the `void* -> uint8_t*` casts in xmemrchr. The proof is
    sound there because the function and its contract use only the uint8 view, and there
    are no writes. The planted-bug control shows the cost: an equivalent `char`-view
    rewrite of xmemrchr is also rejected.

## Planted bugs (mutants.toml, run_mutants.py)

25 mutants on the C code only. The runner checks that stripping ACSL leaves a difference.
WP runs on the mutated function only, at `-wp-par 2` and timeout 60. Results are in
`mutants_result.tsv`.

- **Real bugs: 20/20 caught.** These are off-by-one NULs and ends, pre/post-increment,
  over-read, a missing skip (non-termination), a missing NUL, short padding, a wrong
  return pointer, strlcpy `MIN(slen, dsize)`, `dsize > 1`, xstrlcat returning the stored
  length, xstrlcat dropping the NUL, xmemrchr `--len`, a uint8/int8 signedness bug,
  strequal NULL, and strnequal `n - 1`.
- `xmemrchr-signed-compare` is caught, but it is not counted as evidence. The equivalent
  control `xmemrchr-char-view-control` is also rejected, because of Typed+Cast. The real
  signedness test is `xmemrchr-int8-c`, which is caught.
- **Equivalent: 4/4 survive (fully proved), as they should.**
  - memchrsub split increment.
  - memcnt without `!= NULL`.
  - xstrlcat `>=` boundary.
  - xstrlcat-trunc-overflow, which I first predicted "caught". It is equivalent: the
    extra byte is in bounds and the next statement overwrites it with NUL. WP was right.
- Score: 20/20 non-equivalent caught (19 count as semantic evidence), 0 survivors that
  need explaining.

Note: `mutants_result.tsv` was assembled from the full run plus an `IDS=` rerun of the 3
mutants added afterwards. In the full run, `xstrlcat-trunc-overflow` was still marked
"caught" before I reclassified it. A clean full rerun is
`python3 -I run_mutants.py <nvim> 60` (about 45 minutes at -wp-par 2).

## Reproduction

- Baseline: `run_wp.sh` with `-wp-par 2` gives every goal proved, 333 in total
  (lemmas 2, count_le 9, count_gap 9, then the 15 functions: 11, 11, 12, 10, 36, 32, 36,
  35, 15, 25, 18, 26, 20, 13, 13). Exit 0.
- Probes, stub harnesses and equivalence files are in `review/`. Run each with
  `frama-c -machdep x86_64 -cpp-extra-args="-I stubs" <file> -wp -wp-model Typed+Cast
  -wp-prover z3,cvc5 -wp-par 2`, from a directory holding a copy of `wp/stubs`. For the
  probe scripts, first build `mem.c` with `wp/build.py`, then select the probes with
  `-wp-prop=<names>`.
