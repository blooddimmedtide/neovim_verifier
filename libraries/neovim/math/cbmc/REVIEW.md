# Independent review: CBMC proof of src/nvim/math.c

Reviewer: fresh adversarial reviewer (Claude), 2026-11-02.
Upstream: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. Tool: CBMC 6.4.1, x86_64.

## Verdict: accept with changes

The proof is sound and non-vacuous. Each spec in `harness.c` matches the doc comments
and the real callers. The builtin and fallback builds really are different code, and both
are proved. All 17 non-equivalent planted bugs were caught. The changes below are wording
changes to CLAIM.md. Nothing in the harness has to change.

## Blocking findings

None.

## Required changes (CLAIM.md wording; do not block the proof)

1. **The MSVC `xctz` path is not covered, and CLAIM.md does not say so.** On Windows,
   `cmake.config/CMakeLists.txt:89-92` sets `HAVE_BITSCANFORWARD64`. MSVC defines neither
   `__GNUC__` nor `__clang__`, so its `xctz` uses `_BitScanForward64`. That is a third code
   path, and no harness covers it. The `--fallback` build covers MSVC's `xpopcount` (the
   loop), but its `xctz` loop only covers non-GCC, non-Clang, non-MSVC compilers. CLAIM
   "What the proof relies on" item 4 lists only NetBSD `popcount64`. Add the
   `_BitScanForward64` path there, and change the front-matter `platform:` line so that
   "portable fallback loops" does not read as covering Windows.
2. **The "Planted bugs (own)" evidence row points to "see thread notes".** Nobody can
   reproduce it from the repository. Either commit those mutants or say they are not
   recorded. The reviewer's mutants are now in `cbmc/mutants.toml`.

## Evidence

- **Baseline.** `bash cbmc/run_cbmc.sh <nvim>`: 10/10 proved (5 harnesses × builtin and
  fallback), about 10 s.
- **The two builds compile different code.** `cbmc --preprocess` of the harness gives
  `__builtin_ctzll` and `__builtin_popcountll` in the builtin build, and only the two
  `count++` loops in the fallback build. The `build.py` outputs differ only in the
  `#undef __GNUC__` / `#undef __clang__` lines after the prelude. The `run_cbmc.sh`
  2-argument path injects the same lines with sed. This is confirmed by the mutants that
  touch only the fallback code: they fail only in the fallback build, and the mutants that
  touch only the builtin code fail only in the builtin build.
- **Vacuity probes** (`rev-math/probe.c`, a copy of the harness with extra
  `assert(false)`-style checks, run on both builds). Every probe was refuted, so CBMC can
  reach every branch:
  - all 5 FP classes, and −0.0
  - ctz on x == 0, and r = 0 and r = 63
  - popcount of 0 and of 64
  - append_digit on the fits branch and the overflow branch, at the exact edge
    `INT_MAX/10` with d = 7 (fits) and d = 8 (overflows)
  - trim above, below and inside the range
- **Concrete cross-check against independent references** (`rev-math/xcheck.c`, gcc -O1,
  both builds, 20M random and biased bit patterns): `xfpclassify`/`xisinf`/`xisnan` vs
  glibc `fpclassify`/`isinf`/`isnan`; `xctz` vs `__builtin_ctzll`; `xpopcount` vs
  `__builtin_popcountll`; `trim_to_int` vs a clamp; `vim_append_digit_int` exhaustively
  around `INT_MAX/10`. 0 mismatches.
- **Specs vs intent.**
  - `xfpclassify` is checked against `__CPROVER_isnand`, `__CPROVER_isinfd`,
    `__CPROVER_isnormald` and `== 0.0`. These do not use the code's bit test, and
    `nondet_double` ranges over all 2^64 bit patterns, so every NaN payload and both
    zeros are included.
  - Callers: `eval/encode.c` switches on the FP_* values from the same `<math.h>`, and
    `strings.c` and `funcs.c` use `xisinf`/`xisnan` as booleans. The harness asks for
    exactly 0/1. That is stricter than the callers need, and the code meets it.
  - `xctz` is checked by its defining property (bit r set, bits below r clear), not
    against a builtin. `xpopcount` is checked against an independent bit loop.
- **Precondition of `vim_append_digit_int`.**
  - The only caller is `normal.c:2641`, in `nv_z_get_count`. It is entered only when
    `ascii_isdigit(nchar)` (`normal.c:2734`), so `n = nchar - '0'` starts in 0..9. After
    that, `n` is only changed by `/= 10` or by a successful append, and the digit is
    always `nchar - '0'` with `ascii_isdigit`.
  - So the precondition `v >= 0, 0 <= d <= 9` holds at the only call site, and nothing
    the caller can pass is excluded.

## Non-blocking notes

- **The doc comment promises more than the function does.** It says "add a digit safely
  to an int value", but the function is only safe for `v >= 0` and `0 <= d <= 9`. A
  negative `v` overflows `x * 10`, and a negative `d` can overflow `INT_MAX - digit`.
  CLAIM item 3 states this correctly. This is a latent upstream weakness, not a proof
  defect. A one-line upstream doc fix or assert might be worth suggesting.
- **The proof is for x86_64 (LP64) only.** Mutant `pop-builtin-long` (`__builtin_popcountl`)
  is equivalent here but would be a real bug on LLP64 (MinGW). That is fine, because the
  upstream code uses the `ll` builtins, but it shows that the platform line matters.
- **`run_cbmc.sh` leaks its `mktemp -d` directory** when `build.py` fails (`exit 1`
  before `rm -rf`). This is cosmetic.
- **`xpopcount` on NetBSD (`popcount64`) is excluded**, as CLAIM states.
- **The proof trusts CBMC's models** of `memcpy` and of `__builtin_ctzll` /
  `__builtin_popcountll`. The gcc cross-check above independently backs up the builtin
  build.

## Mutant score

21 mutants (`cbmc/mutants.toml`), each run with `bash run_cbmc.sh <nvim> <mutated copy>`,
which proves both builds:

- **Non-equivalent mutants:** all 17 caught, and every result matched the prediction.
  They cover all 7 functions and both builds: 4 mutants only in the builtin code or only
  in the fallback code, each caught only by the build that compiles it.
- **Survivors:** 4, all predicted equivalent, and CBMC proves each one against the full
  spec:
  - `isnan-self-compare`: `d != d` is the IEEE 754 NaN test.
  - `pop-builtin-long`: `long` is 64-bit on LP64.
  - `digit-reject-negative`: it only differs when `v < 0`, which the precondition
    excludes.
  - `trim-ge-max`: `INT_MAX` clamps to itself.
- **Harness gaps found:** 0.

Scratch files (probes, cross-check, mutated copies and logs):
`/tmp/claude-0/-home-claude/6d24df0b-9d65-5d89-84cb-9e71c7c76de6/scratchpad/rev-math/`.
