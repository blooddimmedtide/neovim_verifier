# Independent review: CBMC proof of sha256.c

Reviewer: fresh adversarial reviewer (Claude), 2026-11-02. Checkout: upstream 7b87ce8.
Scope: CLAIM.md, cbmc/ (spec.h, harness*.c, build.py, check_structure.py, run_*.sh, stubs/),
difftest/, ../findings/sha256-length-over-8gib.md, the fork's diff (branch `verified`).
Files added by the review: `REVIEW.md`, `mutants.toml`, `run_mutants.py`.

## Verdict: **accept with changes**

What holds:

- **Reproduced on upstream:** check_structure (98 statements), run_cbmc.sh (6 harnesses,
  41 s), run_finish.sh (87 s) and run_bytes.sh (1 s) all prove. run_stream.sh was rerun
  only as the reachability-probe variant below (about 40 min under load), with no failure
  except the probes.
- **The spec is right.** I recomputed K from the cube roots of the first 64 primes and H(0)
  from the square roots of the first 8, in exact integer arithmetic, and both equal
  `spec.h`. Σ0 (2, 13, 22), Σ1 (6, 11, 25), σ0 (7, 18, >>3), σ1 (17, 19, >>10), Ch, Maj, the
  big-endian W[0..15], the schedule, the round update and the feed-forward match FIPS 180-4
  4.1.2, 4.2.2, 5.3.3, 5.1.1 and 6.2.2. The padding in harness_finish.c (0x80, zeros to 56
  mod 64, 64-bit big-endian 8T) matches 5.1.1.
- **No harness is vacuous** (probes below).
- **Every ordinary planted bug is caught:** all 24 non-adversarial mutants (10 in
  sha256_process, 5 in sha256_update, 5 in sha256_finish, 4 in sha256_bytes) are caught by
  a proof check. The self-test-vector mutant is caught by the native run.

What fails:

Planted bugs of two kinds pass every proof check. The differential test catches all of
them. Because of that, two statements in CLAIM.md are false as written:

- "Nothing else may be in the body" is false. `#define` lines in the body are thrown away
  unread, and text outside the body is never looked at (**B1**).
- "Together with the sha256_process proof this gives SHA-256 of the whole input" does not
  follow from what is proved. No harness says that `ctx->state` reaching the next
  compression is the state the previous one left (**B2**).

Neither gap hides a bug in Neovim. I read the 300-line file and it does neither thing, and
the differential test agrees. The gaps are in the argument. Each can be closed with a small
change to a script or harness. Until that is done, the strength must not become
full-correctness, or CLAIM.md must state the two assumptions.

## Blocking findings

**B1. check_structure.py plus the macro harnesses can be fooled by preprocessor text (major).**
The meaning of the macros is proved in harness.c (h_prims, h_round, h_sched, h_endian).
Those harnesses come after `#include SHA256_C`, so they see the **last** definition of
each macro in the file. That need not be the definition the body of sha256_process
expanded. check_structure.py does not close the gap:

- It deletes every `#define` line in the body without reading it.
- It never looks outside the body.
- It removes `//` comments before joining backslash-newline lines. C does it the other
  way round (translation phase 2 comes before phase 3).

Two planted bugs pass check_structure.py and all of run_cbmc.sh:
- `proc-macro-redefined-later`: the body uses an S3 (Σ1) with rotation 26. After the
  function, `#undef S3` and the correct `#define S3` are added. h_prims checks the correct
  one.
- `proc-comment-splice`: `ctx->state[6] += G;  // and H, below: \`. In C, the backslash
  splices the next line, `ctx->state[7] += H;`, into the comment. The script still counts
  that line as a statement.

The same trick works for GET_UINT32 (defined outside the body), R and P. A `#define A B` in
the body is also dropped unread.

Required fix, in check_structure.py:
1. Splice backslash-newlines first (`src.replace("\\\n", "")` applied the way the
   preprocessor does it, or reject any `\` at the end of a line outside a `#define`).
2. Then strip `//` and `/* */` comments.
3. Require that the body's `#define` names are exactly {SHR, ROTR, S0, S1, S2, S3, F0, F1,
   R, P}.
4. Require that the whole file has exactly one `#define` for each of those and for
   GET_UINT32/PUT_UINT32, and no `#undef` or conditional directive after the includes.

Also recommended: a cheap concrete check of the real sha256_process against
`spec_compress`, for example h_process on two or three fixed blocks and states (constant
propagation makes it fast), or the FIPS vectors through sha256_bytes in CBMC. It ties the
actual body to the spec independently of any text matching.

**B2. No frame condition on the context between calls (major).** The recorders check the
bytes and the context *pointer* passed to sha256_process. Nothing relates the *contents*
of `ctx->state` at one call to what the previous compression produced. After this fix,
three planted bugs should be caught. Today they all prove:

- `fin-state-scribble`: sha256_finish does `ctx->state[0] ^= last` before padding. h_finish
  is proved, because the digest is compared with whatever state is there at the end.
- `upd-state-scribble`: sha256_update does `ctx->state[7] += left`. h_update has no
  assertion about `ctx->state` at all, and the loop's assigns clause lets the loop write
  all of it. h_update is proved on this mutant.
- `bytes-ctx-scribble`: sha256_bytes sets `ctx.total[0] = buf_len` before finish. h_bytes
  is proved, because rec_start/rec_update/rec_finish track only the pointer.
  Difftest: 608 of 4000 digests wrong.

Required fix:
- In harness_stream.c and harness_finish.c, keep a shadow `rec_state[8]`, set from
  `ctx->state` at harness start. rec_process asserts `ctx->state == rec_state` on entry,
  then havocs `ctx->state` and copies the new value into `rec_state`.
- h_update ends with `ctx->state == rec_state`. The loop invariant gains the same
  equality, and `rec_state` goes into the assigns clause.
- h_finish compares the digest with `rec_state`, not with `ctx->state`.
- In harness_bytes.c, rec_start/rec_update havoc the whole context and save a copy, and
  rec_update/rec_finish assert that the context is unchanged on entry.

That turns "only sha256_process changes the state" from a reading of the code into a proved
fact. Without it, CLAIM.md must list it as an assumption in "What the proof relies on".

## Non-blocking findings

1. **Evidence for the fork (resolved during review).** When the review started, the row
   "update, fixed fork (every len)" held the placeholder `H_UPDATE_FIXED`. Commit d84327f
   replaced it with "proved". I did not rerun it. Add the run time, as the other rows do.
2. **"every size_t length" on the fork (minor).** CBMC uses 8 object bits by default, so
   pointer offsets have 56 bits. With `-DSHA256_FIXED`, `malloc(len)` and `in + len` for
   `len >= 2^56` are outside what CBMC models faithfully. x86_64 objects are below 2^47
   bytes, so nothing real is lost. Say "every length an object can have" and add the 56-bit
   offset model to the trusted base, or bound `len < 2^56` in the harness.
3. **Check flags (wording).** "no overflow" should be "no signed overflow and no undefined
   shift". Unsigned wraparound is intended and not checked. `--pointer-overflow-check` and
   `--pointer-primitive-check` are not used. Adding them costs little on h_finish and
   h_bytes.
4. **Dead and misleading references to h_process (wording).** The header of
   harness_stream.c says "h_process + check_structure.py prove the real sha256_process".
   h_process is never run (CLAIM.md says it does not finish), and `spec_compress` is used by
   no proof that runs. Fix the comment, and mark h_process in harness.c as not run (or
   replace it with the concrete-block variant from B1).
5. **The rotation argument is on paper (low).** check_structure.py confirms that round t
   calls P with the names rotated right by t and that `state[i] += names[i]`. The step from
   that to FIPS's shift (`h = g; ...; e = d + T1; ...; a = T1 + T2`) is a hand argument.
   I checked it: P(a..h) leaves the new *a* in the old *h* slot and the new *e* in the old
   *d* slot, and 64 ≡ 0 (mod 8) brings the names back to A..H. It is correct, and it should
   be listed as part of what is trusted in step 6.
6. **Weak sha256_bytes check in difftest (low).** difftest.py accepts either
   `sha256(whole)` or `sha256(prefix)` whenever `cut < len`, because dt.c does not print
   whether it passed the salt. A sha256_bytes that ignored the salt, or hashed it when it is
   NULL, would pass. Print the choice in dt.c. h_bytes covers this in the proof.
7. **Loop contract (no issue).**
   - The assigns clause (`length, input, rec_calls, ctx->state`) is exactly what the body
     writes once process is replaced. DFCC checks it. `left`, the buffer and the recorder's
     snapshots are outside it, so they are preserved without being stated.
   - The invariant pins `input`, `length`, `left` and the call count. Together with the exit
     condition, that gives the postconditions, and the probes show the end of h_update is
     reached.
   - `decreases(length)` is right.
   - The only thing the invariant does not carry is `ctx->state` (B2).
   - The invariant-breaking mutant `upd-input-step-63` is caught.
8. **snprintf model (accepted).** The model matches C11 7.21.6.1 for `"%02x"`, an int in
   0..255 and n ≥ 3. It asserts the format string and the range, so a format mutant is
   caught (`bytes-uppercase`).
9. **sha256_self_test argument (accepted).** It has no inputs, and its two statics are
   covered by the first and second calls in dt.c. The "failures branch is dead" step relies
   on the hash being correct, so it inherits B1 and B2. Today the native run is the evidence
   for it, and it does fail on a wrong vector (`selftest-vector`).
10. **Finding (accepted).** For a single call with `2^32 <= len < 2^33`, the carry test
    always adds exactly 1. That is right unless the low word also carries. For
    `len >= 2^33`, high bits are lost. This matches the finding. The fork's fix adds the
    high word and fixes the carry test (`< len_lo`). The upstream harness assumption
    `len <= 0xFFFFFFFF` is exactly the range where upstream is correct.

## Non-vacuity probes

I copied the harnesses to the scratch directory, added probe asserts that must FAIL if the
location is reachable, and used the same scripts and flags. Every probe failed, so every
location is reachable, and no other assertion failed.

| Harness | Probe (assert that must fail) | Result |
|---|---|---|
| h_sched | `t != 63` after the checks | FAILURE (reachable) |
| h_endian | `i != 4` after the checks | FAILURE |
| h_bytes | `0` at the end; `exp_salt == NULL` at the end (the salt path is reached) | FAILURE, FAILURE |
| h_finish | `0` at the end; inside rec_process `rec_calls != 0` and `rec_calls != 1` (a 2-block padding is reached) | FAILURE x3 |
| h_update (`-DNO_BLOCK_CHECK`) | `0` at the end | FAILURE |
| h_update | `len < 2^32-64 \|\| rec_calls < 3` at the end (near-4 GiB lengths reach the end) | FAILURE |
| h_update | inside rec_process: `data != ctx->buffer` (the buffered first block is reached) | FAILURE |
| h_update | inside rec_process: a loop block with `rec_calls >= 3` (the loop body under the contract is reached) | FAILURE |
| h_update | inside the tail check: `0` | FAILURE |

There is no contradictory `__CPROVER_assume`. The nondeterministic index `rec_b < 64` is
fixed per run but universally quantified, and it is used for every block, so every byte
of every block is covered. The same holds for the tail index `i`.

## Planted bugs

There are 30 mutants (`mutants.toml`), run with `python3 -I run_mutants.py <nvim>`
(`IDS=a,b` runs a subset). A sha256_update mutant expected to be caught by the count or by
the invariant runs with `-DNO_BLOCK_CHECK -DNO_TAIL_CHECK`, and one expected to be caught
by the tail check runs with `-DNO_BLOCK_CHECK`. A failure found with fewer asserts is still
a failure. `upd-state-scribble` runs with both flags. The asserts that are dropped only
compare bytes, and that mutant changes no byte.

| id | function | expected | result (proof checks) | difftest |
|---|---|---|---|---|
| `proc-k20` | sha256_process | caught | caught (check_structure: statement 46, K) | - |
| `proc-Sigma1-rot26` | sha256_process | caught | caught (h_prims S3 = Sigma1, h_round) | - |
| `proc-sigma0-shr-as-rotr` | sha256_process | caught | caught (h_prims S0 = sigma0, h_sched) | - |
| `proc-ch-or` | sha256_process | caught | caught (h_prims F1 = Ch, h_round) | - |
| `proc-rotr-31` | sha256_process | caught | caught (h_prims S0..S3, h_round, h_sched) | - |
| `proc-sched-t7` | sha256_process | caught | caught (h_sched) | - |
| `proc-maj-arg` | sha256_process | caught | caught (h_round) | - |
| `proc-round39-names` | sha256_process | caught | caught (check_structure: statement 65) | - |
| `proc-get-le` | sha256_process | caught | caught (h_endian: get) | - |
| `proc-final-add` | sha256_process | caught | caught (check_structure: statement 95) | - |
| `proc-macro-redefined-later` | sha256_process | survives | survives check_structure and all of run_cbmc.sh | caught |
| `proc-comment-splice` | sha256_process | survives | survives check_structure and all of run_cbmc.sh | caught |
| `upd-carry-le` | sha256_update | caught | caught (byte count) [-DNO_BLOCK_CHECK -DNO_TAIL_CHECK] | - |
| `upd-fill-off-by-one` | sha256_update | caught | caught (every complete block processed; the rest is buffered; only whole blocks) [-DNO_BLOCK_CHECK] | - |
| `upd-tail-offset` | sha256_update | caught | caught (the rest is buffered) [-DNO_BLOCK_CHECK] | - |
| `upd-input-step-63` | sha256_update | caught | caught (loop invariant after step) [-DNO_BLOCK_CHECK -DNO_TAIL_CHECK] | - |
| `upd-skip-buffer-block` | sha256_update | caught | caught (loop invariant before entry; every complete block processed) [-DNO_BLOCK_CHECK -DNO_TAIL_CHECK] | - |
| `upd-state-scribble` | sha256_update | survives | survives h_update (proved) [-DNO_BLOCK_CHECK -DNO_TAIL_CHECK] | caught |
| `fin-pad-0x01` | sha256_finish | caught | caught (block = padded stream) | - |
| `fin-padn-le56` | sha256_finish | caught | caught (all padded blocks processed; block = padded stream) | - |
| `fin-bitlen-shift` | sha256_finish | caught | caught (block = padded stream) | - |
| `fin-msglen-swapped` | sha256_finish | caught | caught (block = padded stream) | - |
| `fin-digest-word` | sha256_finish | caught | caught (digest = state, big-endian) | - |
| `fin-state-scribble` | sha256_finish | survives | survives h_finish (proved) | caught |
| `bytes-hex-step` | sha256_bytes | caught | caught (hex digits) | - |
| `bytes-uppercase` | sha256_bytes | caught | caught (snprintf model: only %02x used) | - |
| `bytes-salt-inverted` | sha256_bytes | caught | caught (then salt; finish after the input) | - |
| `bytes-last-byte` | sha256_bytes | caught | caught (hex digits) | - |
| `bytes-ctx-scribble` | sha256_bytes | survives | survives h_bytes (proved) | caught |
| `selftest-vector` | sha256_self_test | caught | caught by difftest only (SELFTEST FAILED); no proof covers it, as CLAIM.md says | caught |

## Required changes to CLAIM.md

1. In "How sha256_process is proved", step 6: replace "Nothing else may be in the body (98
   statements)". The new text should say that `#define` lines are not read, and that
   h_prims, h_round, h_sched and h_endian check the definitions visible at the end of the
   file. Keep this until B1 is fixed, then describe the new checks.
2. In "How the stream functions are proved": after "this gives SHA-256 of the whole
   input", add the assumption "provided nothing but sha256_process writes `ctx->state`
   between the calls, and sha256_bytes does not change the context between its calls
   (read from the code, not proved)". Add the same item under "What the proof relies on".
   Remove both once B2 is fixed.
3. Add to "What the proof relies on":
   - the paper step "names rotated by t ⇒ FIPS's variable shift" (non-blocking 5);
   - for the fork's every-length claim, CBMC's 56-bit offsets (non-blocking 2).
4. "no out-of-bounds access, no overflow" becomes "no out-of-bounds access, no signed
   overflow, no undefined shift".
5. Evidence: add the time to the fork row (now "proved", d84327f).
6. Evidence rows "Independent review" and "Planted bugs": point to this file and
   `mutants.toml`. Report 30 mutants. The 24 non-adversarial ones are caught by the proofs. The 2
   preprocessor tricks (B1) and the 3 context scribbles (B2) survive the proofs and are
   caught by difftest. The self-test-vector mutant is caught by difftest only, as stated.
7. "Planted bugs in the K table, the argument order and the macros are all caught": qualify
   with "unless a macro is redefined outside the body (B1)", or drop the sentence once B1 is
   fixed.
