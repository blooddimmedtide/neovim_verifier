# Review: regexp.c number readers (getdecchrs, gethexchrs, getoctchrs)

Independent adversarial review (AGENT_PROMPT.md step 6). Upstream 7b87ce8, fixed fork
3336e2d (getdecchrs identical at the branch head b2bbb00). Line numbers below are the fixed fork's.

**Verdict: accept with changes.** The getdecchrs WP contract is functional, complete
(two disjoint behaviours, `assigns regparse, curchr`) and tight on memory (readable only up to
the first non-digit). The hex/oct CBMC proofs are functionally right but prove memory safety under
a weaker-than-real input model (issue 1), and the differential test cannot fail (issue 2). All 22
non-equivalent mutants aimed at the proofs were caught; the two survivors that are not equivalent are
exactly the issue-1 gap.

## Issues, most severe first

1. **(Medium) hex/oct harnesses make more memory readable than callers guarantee.**
   `h_gethexchrs` allocates exactly `max` bytes and `h_getoctchrs` exactly 3, all readable, whatever
   the content. Callers only guarantee a NUL-terminated pattern (CLAIM.md item 3: "readable memory up
   to the first non-digit"). A function that reads `regparse[1]` while `regparse[0]` is the pattern's
   NUL (e.g. `\%x` or `\%o` at the very end of the pattern, at the end of its allocation) passes the
   proof. Planted: `hex-read-past-nul`, `oct-read-past-nul` (same values, extra read) — both
   **survived**. The real code does not do this, but the proof does not show it, so CLAIM's row
   "Reads only `regparse[0 .. max-1]`" is true but is not the property callers need.
   Fix: give the harness a NUL-terminated string of nondet length, e.g.
   `size_t len` in `1 .. max+1` (oct: `1 .. 4`), `buf = malloc(len)`, `buf[len-1] = 0`, other bytes
   arbitrary; and state in CLAIM that only bytes up to the first non-digit (and at most max) are read.
   Then both gap mutants should be caught.

2. **(Medium) `difftest/run_difftest.sh` always exits 0 on mismatches.** The line
   `"$W/dt" | tail -1 || status=1` tests `tail`'s status, not `dt`'s (no `pipefail`). Every
   mutant in `mutants_result.tsv` with mismatches > 0 shows `exit=0` (e.g. `hex-empty-test`,
   157,329 mismatches, exit 0). The CLAIM evidence row is correct only because someone read the
   number; in CI this check cannot fail. Fix: `set -o pipefail`, or capture the output and test
   the program's exit code.

3. **(Low) CLAIM/finding slightly overstate what is proved about the fix.** "Fixed in the fork and
   proved for every input" — only `getdecchrs` is proved. Commit 3336e2d also changes two callers
   (`regpiece` line 5291 `nr < 0 || nr > INT_MAX`, `nfa_regpiece` line 11020
   `EMIT(c2 > INT_MAX ? 0 : (int)c2)`), and the fix relies on "every caller rejects or clamps values
   above INT_MAX". Neither is proved or tested here. I checked every caller by hand and the
   claim holds (see "Caller check" below), but CLAIM should say the caller side is reviewed, not proved.

4. **(Low) No frame condition for gethexchrs/getoctchrs.** The CBMC standalone file declares only
   `regparse`, so "changes nothing but `regparse`" (in particular not `curchr`, unlike getdecchrs) is
   not checked; a mutant writing `curchr` would fail to compile rather than be caught. By reading
   the code: both write only `regparse` and locals. Fix: declare `curchr` (and maybe a sentinel
   global) in the prelude and assert it is unchanged.

5. **(Low) Differential test coverage holes.** The alphabet `0179afAFgG/:@`\x80\xff` has no `8`
   (the octal edge) and no strings like `21474836470` / `2147483647` + digit. Mutants
   `dec-guard-lt`, `oct-limit-le`, `oct-limit-037` give 0 mismatches. Proofs catch them; this
   only matters for the difftest's value as a cross-check of the reference.

6. **(Info) WP is incomplete on two equivalent rewrites.** `dec-guard-dropped` (drop the redundant
   `nr <= INT_MAX` guard) and `dec-signed-read` (drop the `(uint8_t)` cast) are semantically
   equivalent but `loop_invariant_5_preserved` (the saturated value invariant) times out at 60 s.
   Not a soundness problem; noted so nobody reads "caught" as "bug".

7. **(Info) run_wp.sh header says CVC5 runs behind `tools/bin/cvc5-fsq`, but the script calls the
   plain `cvc5` on PATH.** All goals prove with plain CVC5 anyway. Fix the comment or the script.

## What I checked and found sound

- **Spec vs documentation.** getdecchrs: "Return -1 for invalid. Consumes all digits." — matched
  (k = 0: -1, nothing moved, curchr kept; k > 0: exactly k consumed, curchr = -1, value or
  INT_MAX + 1). gethexchrs: longest run of at most max hex digits, -1 if none. getoctchrs: at most 3
  octal digits, value <= 0377, "400 is treated as 40", 8/9 not digits — the harness writes the stop
  rule as `v*8 + d <= 0377`, a different formulation from the code's `nr < 040`, so it is not copied.
- **References are independent.** `dval` is the positional value in ACSL over `unsigned char`;
  `spec_hexdigit` is a switch table; neither uses `hex2nr`/`ascii_isxdigit`. `INT_MAX + 1` and -1
  come from the doc comment/fix, as CLAIM says.
- **Preconditions vs callers.**
  `gethexchrs` is called only with literal 2, 4, 8 (lines 4749-4753, 5743-5747, 10395-10399).
  `getdecchrs` callers: 4745 (`\%d`, bt), 5263 (`\@`, bt), 5739 (`coll_get_char`, both engines via
  4914/4964/10729), 10391 (`\%d`, NFA), 10984 (`\@`, NFA). All read from `regparse` inside the
  NUL-terminated pattern, so `dec_run(regparse, k)` holds with k = digits before the NUL/non-digit.
- **Caller check (results).** `\%d/o/x/u/U`: `i < 0 || i > INT_MAX` -> E678 in both engines, so
  INT_MAX + 1 and `\%U` values above 0x7FFFFFFF are rejected. `coll_get_char`: `< 0` -> backslash,
  `> INT_MAX` -> INT_MAX. `\@`: bt `nr < 0 || nr > INT_MAX` -> 0 (no limit); NFA `c2 > INT_MAX` -> 0
  and -1 stays -1, and `state->val <= 0` means no limit (line 13953). The k = 0 "curchr unchanged"
  behaviour matters for `\@=` (no number) and is in the contract.
- **Upstream contract** is the same functional spec under `k <= INT_MAX && dval <= INT64_MAX`,
  which is exactly the overflow boundary of `int i` and `int64_t nr` (finding confirmed).
- **Tool runs reproduce CLAIM**: WP fixed 15/15 + 41/41, upstream 15/15 + 43/43; CBMC 4/4;
  difftest 351,505 / 279,620 checks, 0 mismatches.

## Planted bugs

`mutants.toml` (29 mutants), `run_mutants.py`, results in `mutants_result.tsv`.
`run_mutants.py` copies the three source files of the chosen checkout, mutates the function,
re-pins its sha256 in a copy of `wp/build.py` or `cbmc/build.py`, and runs the unchanged proof
script (WP for getdecchrs, CBMC with `ONLY=<harness>` for hex/oct); build refusals are reported
separately, never counted as caught. The difftest column is information only (see issue 2).

| Group | Caught | Survived | Equivalent |
|---|---|---|---|
| getdecchrs fixed (WP) | 10/10 | 0 | 2 (both "caught" by WP timeout, issue 6) |
| getdecchrs upstream (WP) | 2/2 | 0 | 0 |
| gethexchrs (CBMC) | 4/4 | `hex-read-past-nul` (gap, issue 1) | 2 (survived) |
| getoctchrs (CBMC) | 6/6 | `oct-read-past-nul` (gap, issue 1) | 1 (survived) |

Every non-equivalent mutant aimed at the stated properties is caught. The two survivors are
real memory-safety bugs under the callers' NUL-terminated input that the current harness model
cannot see; they must be caught once issue 1 is fixed (change their `expect` to "caught" then).

## Resolution (thread author, after the review)

1. Fixed: `cbmc/harness.c` now gives each function a NUL-terminated string of every length 1..max+1
   (oct 1..4), allocated exactly, so a read past the NUL fails. `hex-read-past-nul` and
   `oct-read-past-nul` are now caught (`expect = "caught"`).
2. Fixed: `run_difftest.sh` takes the exit status of the test binary itself; `hex-empty-test`
   now gives exit 1.
3. Fixed: `CLAIM.md` and the finding say only `getdecchrs` is proved; the caller changes are
   reviewed by hand (this review) and tested.
4. Fixed: both harnesses check that the input bytes are unchanged; `regparse` is the only
   global in the extracted file, so no other global can be written.
5. Fixed: the difftest alphabet has `8`, and the edges include `21474836470x`, `21474836479`,
   `2147483646x` and `21474836480`.
6. No change (prover gap on equivalent mutants).
7. Clarified: `-wp-prover cvc5` runs `tools/bin/cvc5-fsq` because `tools/install.sh` points
   Why3's CVC5 entry at it; the header now says so.

