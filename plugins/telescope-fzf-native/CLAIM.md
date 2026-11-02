---
entry: telescope-fzf-native.nvim src/fzf.c (the whole C core, 1272 lines)
upstream: https://github.com/nvim-telescope/telescope-fzf-native.nvim
commit: b25b749b9db64d375d782094e2b9dce53ad53a40
fixed_copy: upstream + findings/fix.diff (two out-of-bounds reads), sha256 b65aa701…53621a4
fixed_copy_2: fixed copy + findings/fix-v2-stale-slab.diff (stale slab memory in v2), sha256 4db1b499…30cc2f2d
toolchain: CBMC 6.4.1 (+ Z3 for three harnesses), Frama-C 33 WP with Z3 and CVC5 (--full-saturate-quant), gcc with ASan/UBSan
strength: bounded (CBMC) for the algorithms and the interface; unbounded (WP) for 14 helpers; not yet reviewed
platform: x86_64, char signed; locale classifying bytes like "C"
---

# Claim card: telescope-fzf-native src/fzf.c

The proved file is `fzf.c` itself, unchanged: the CBMC harnesses `#include` it (its sha256
is printed and compared with the reviewed versions), and the WP build copies the exact text
of each helper (sha256 pinned) with ACSL in comments only (stripping them gives the text back).

"Bounded" below means: proved by CBMC for **every** input up to the stated sizes (every byte
value, NUL included, both case modes, normalize on and off, `pos` NULL or an array of any
capacity and fill, slab NULL or of any capacity with arbitrary stale contents), with all loops
completely unwound (unwinding assertions). "Unbounded" means a Frama-C WP proof for every length.

## Specification

`cbmc/spec.h` (scoring, classes, the five match algorithms), `cbmc/spec_parse.h` (pattern
syntax) and `wp/contracts.py` are written from fzf's algorithm (`algo.go` of the version this is
a port of: constants, `bonusFor`, `calculateScore`, `FuzzyMatchV1`, `ExactMatchNaive`,
`PrefixMatch`, `SuffixMatch`, `EqualMatch`, extended-search syntax) in a different form from
the C code (e.g. v1 as "shortest prefix that contains the pattern, then latest start"; exact as
"best-bonus occurrence, earliest among ties"; the score as a sum over matched chars, chunks and
gap runs). Validation of the spec itself: with the five references put in place of the C
algorithms, the plugin's own test suite (`test/test.c`, the 53 tests that do not compare
function pointers) passes (`difftest/upstream_tests`).

Where this port deliberately or accidentally differs from fzf, the spec states the port's
behaviour and the difference is listed in `findings/v2-stale-slab-and-other-findings.md` §4.

## What is proved

| Function | Property | How |
|---|---|---|
| `index_byte` | index of the first `b` in `data[0..size)`, else -1 (size < 2^31) | WP unbounded; CBMC |
| `leading_whitespaces`, `trailing_whitespaces` (fixed) | length of the maximal white prefix / suffix (C-locale white) | WP unbounded; CBMC |
| `copy_runes`, `copy_into_i16` | copies `size` elements (char sign-extended), writes nothing else | WP unbounded; CBMC |
| `trim_whitespace_left` | skips leading `' '` but at most ceil(len/2) of them (defect, not observable: see findings) | WP unbounded; CBMC |
| `char_class_of_ascii`, `char_class_of`, `bonus_for`, `bonus_at`, `max16`, `min64u`, `normalize_rune` (identity), `is_ascii` (always true) | equal to the spec functions | WP unbounded; CBMC every input |
| `has_prefix`, `has_suffix` | `strncmp(..) == 0` semantics, suffix needs `len >= suffix_len` | CBMC, strings ≤ 6 |
| `str_tolower` | fresh object of size+1: folded bytes and NUL; input unchanged | CBMC, size ≤ 6 |
| `str_replace_char` (find ≠ 0, replace ≠ 0, find ≠ replace) | every `find` replaced, nothing else changed | CBMC, strings ≤ 6 |
| `str_replace` (its one call: `"\\ "` → `"\t"`) | fresh exact-size string with every non-overlapping occurrence replaced left to right; NULL for empty/NULL arguments | CBMC (Z3), strings ≤ 4 |
| `fzf_pos_array`, `append_pos`, `unsafe_append_pos`, `resize_pos`, `insert_range` | positions appended exactly, old entries kept, capacity real; `insert_range` appends start..end-1 (end ≤ INT32_MAX) | CBMC, capacity ≤ 6 (≤ 3 for insert_range) |
| `alloc16`, `alloc32` | a slab slice (when `cap > offset + size`) or a fresh zeroed buffer, offset advanced only for the slab | CBMC, sizes ≤ 6, slab ≤ 12 |
| `try_skip`, `ascii_fuzzy_index` | first match at/after `from` (a lowercase pattern byte also matches its uppercase form when case-insensitive); fuzzy index = position before the first byte's first match, -1 if the pattern is not a subsequence | CBMC, text ≤ 6, pattern ≤ 3 |
| `calculate_score` | equals fzf's calculateScore on every window whose leftmost occurrence ends at its last byte (the windows its callers pass); appends those positions | CBMC, text ≤ 5, pattern ≤ 3 |
| `fzf_prefix_match`, `fzf_suffix_match` (fixed), `fzf_equal_match`, `fzf_exact_match_naive`, `fzf_fuzzy_match_v1` | **full result (start, end, score) and positions equal the reference**; reads nothing outside text[0..N) and pattern[0..M) | CBMC, text ≤ 5, pattern ≤ 3 |
| `fzf_fuzzy_match_v2` | no UB, no access outside any object (slab, text, pattern, matrices); matches iff the pattern is a subsequence of the folded text; positions: exactly M, strictly decreasing as appended, inside the text, each on a byte folding to its pattern byte, start = first, end = last + 1; score ≥ 16; **full result for 1-byte patterns** (best-bonus occurrence, earliest among ties) and **for the v1 fallback** (slab too small). **Full result and positions equal `ref_v2`**, a separate transcription of fzf 0.27.0's `FuzzyMatchV2` (`cbmc/spec.h`), when the slab is NULL or zeroed (`h_v2_full`). This shows the port matches fzf's algorithm. It does NOT show that fzf's dynamic program is optimal against the `r_score` definition for M ≥ 2: no independent optimality spec was proved | CBMC, text ≤ 5, pattern ≤ 3, slab ≤ 48/12 (`h_v2_noslab`: text ≤ 3) |
| `fzf_fuzzy_match_v2` slab independence | fixed copy: score and end do not depend on stale slab contents, start and positions DO (finding 1); fixed copy 2: result and positions identical with any slab contents and with no slab | CBMC |
| `fzf_parse_pattern`, `fzf_free_pattern` | the parse equals the reference parser (sets, term kinds, inverse, case sensitivity, text, `only_inv`); every allocation freed | CBMC with `--memory-leak-check`, patterns ≤ 4 |
| `fzf_get_score`, `fzf_get_positions`, `fzf_free_positions`, `fzf_make_slab`, `fzf_free_slab` | score = the extended-search combination of the term results (sum of the first matching non-inverse term per AND-set; 0 if a set fails; only-inverse: 1 iff no term matches); positions non-NULL iff every set matches, all inside the text; no leak | CBMC with `--memory-leak-check`, pattern ≤ 3, text ≤ 3 |

All CBMC harnesses check: pointer and bounds checks (every access inside a live object), signed
overflow, undefined shifts, pointer primitives, division by zero, unwinding assertions.

## Findings

New (details and reproducers in `findings/v2-stale-slab-and-other-findings.md`):
1. **v2 positions depend on earlier calls** through stale slab memory (functional bug, reachable
   in every Telescope picker: score with one slab, then highlight with the same slab). Fix:
   `findings/fix-v2-stale-slab.diff`, proved (CBMC) and differential-tested.
2. **A matching long line can score ≤ 0** (v1 fallback, unclamped), which Telescope's
   `1/score` turns into a top rank (negative) or a filtered line (0). Reproducer included.
3. **A line that matches only through an inverse term of an OR group scores 0** (`!a | b`,
   `!a | !b` on `c`), and the sorter hides it. fzf keeps every item whose sets all match,
   whatever the score. `findings/repro_inverse_or.c`.
4. Small deviations: `trim_whitespace_left` (half trim, unobservable), TAB in a pattern means
   space, `^ a$` with a leading-space pattern never matches, v2 `start` with `pos == NULL`,
   `str_replace_char(s, c, c)` loops forever, malloc results unchecked, locale dependence.

Known (from before): the two out-of-bounds reads in `trailing_whitespaces` and
`fzf_suffix_match` — the same harnesses find both on the upstream file (Evidence).

## What the proof relies on

1. **CBMC, Frama-C WP, Why3, Z3, CVC5 are sound** for this code (x86_64 data model).
2. **C library models** (`cbmc/libc_model.c`): isspace/tolower ("C" locale), strtok, strstr,
   memset, strlen, strncmp, strcmp, strchr, strcpy, strncpy, strdup written from C11; checked
   equal to glibc (C locale) on all bytes / 2,000,000 random string cases
   (`difftest/libc_check.c`). CBMC's own memset was replaced because it is wrong on symbolic
   sizes (a zeroed `int16_t[2]` keeps a nonzero byte). malloc, realloc and free are CBMC's.
   WP: `wp/stubs/fzf_ctype.h` (isspace/tolower contracts, "C" locale).
3. **Locale:** bytes are classified as in the "C" locale. glibc UTF-8 locales do so for single
   bytes; Neovim calls `setlocale(LC_ALL, "")`, so a single-byte (Latin-1) locale is not covered.
4. **malloc never fails** (`--no-malloc-may-fail`): the code never checks it.
5. **Implementation-defined conversions** wrap modulo 2^n (GCC/Clang): `(char)tolower(..)`,
   `(int16_t)` scores, `(int32_t)` indices, `(uint8_t)` stores. Not checked (`--conversion-check`
   flags them all).
6. **Bounds:** the CBMC results hold for inputs up to the sizes in the table. Beyond them only
   the differential test speaks (below). Texts must be shorter than 2 GiB (int32 results; above
   that `insert_range`'s `(int32_t)end - (int32_t)start` can overflow, UB).
7. **v2 int16 scores:** with the default slab v2 runs only for N·M ≤ 102,400, so M ≤ 320 and
   scores stay below 32 · 320 < 32,767 (argued, not machine-checked). With a NULL slab or a
   bigger custom slab, long patterns can overflow `int16_t` (implementation-defined wrap).
8. **Preconditions:** text/pattern pointers valid for `size` bytes; `fzf_parse_pattern` gets a
   writable NUL-terminated string (it writes NULs over trailing spaces); `get_score` /
   `get_positions` get NUL-terminated text.

## Not covered

- Score optimality of `fzf_fuzzy_match_v2` for patterns of 2+ bytes, measured against an independent spec. Within the bounds it is only shown equal to the fzf 0.27.0 transcription `ref_v2`. Above the bounds, the differential test compares v2 with `ref_v2` (NULL slab) on random inputs.
- Any input above the CBMC bounds, except by the differential test.
- `fzf_make_default_slab` in CBMC (a 100K-element memset); covered by the differential test.
- The Lua side (`lua/fzf_lib.lua`, the Telescope sorter) beyond reading it for reachability.
- Independent review of spec and harnesses; planted bugs chosen by an independent reviewer
  (the current set in `mutants/` was chosen by the prover).

## Evidence

(filled from the final runs below)
