# Independent review: CBMC proof of src/cjson/strbuf.c / strbuf.h

The reviewer is a fresh adversarial agent with no context from the prover. Target: Neovim 7b87ce8 (upstream) and branch
`claude/project-thread-gritim` (fixed: `size_t i` in `strbuf_append_string`), read with `git show`.
Tools: CBMC 6.4.1 with cadical.

## Verdict: NOT YET. The harness changes listed below are required.

No harness is vacuous: every assertion is reachable. Every proof in `cbmc/run_cbmc.sh` passes on the
fixed code (20/20 runs, both char signednesses, 108 s). The finding is real.

The CLAIM nevertheless overstates several "proved" rows:
- The harness assumptions exclude the **empty string**, **buffers over 16 bytes**, **`buf == NULL`**
  and **`debug != 0`**.
- The allocation model **does not end object lifetimes**, so use-after-free is invisible.

Results: 53 planted bugs, 35 caught. All 8 equivalent mutants survive, as they should. **10 non-equivalent mutants survive**: 9 are
closed by the suggested strengthened harness (`review/harness_review.c`). The 10th is the upstream bug itself
(`append-int-index`). No CBMC bound can catch it, and the unbounded WP proof that CLAIM.md cites is not in the package.

## What I ran
| Check | Result |
|---|---|
| `bash cbmc/run_cbmc.sh <fixed>` | 20/20 proved, 108 s |
| `--cover assertion` on every harness, both signednesses | every user assertion reachable, except the intended `die returned` |
| `review/probes.sh` (targeted `__CPROVER_cover` goals + precondition probes) | see F1–F6 |
| UBSan repro (`findings/...-repro.c`), upstream vs fixed | upstream: `strbuf.c:185:26: signed integer overflow: 2147483647 + 1`; fixed: `length 2147483649 (want 2147483649)` |
| `python3 -I run_mutants.py` | 35/53 caught; 10 non-equivalent survivors (table below) |
| `review/run_review.sh` (strengthened harnesses) on the fixed code | all 20 runs proved: r_helpers ≈ 300 s per signedness, r_append_string ≈ 100 s, the rest ≈ 40 s together |

## Findings

### F1 (high): the free/realloc model never ends a lifetime, so use-after-free is not checked
`cbmc/model.h` replaces `free` with a recorder, and `realloc` leaves the old block alive. CBMC's
`--pointer-check` therefore never sees a deallocated object. Probes `q_uaf_unseen` (read after `free`) and
`q_realloc_stale` (write through the pre-realloc pointer) both verify SUCCESSFUL.

Two plausible bugs survive because of this:
- `free-uaf-order`: `strbuf_free` frees the struct, then reads and writes `s->buf`.
- `fts-uaf-return`: `strbuf_free_to_string` returns `s->buf` after `free(s)`.

These are exactly the bugs a `strbuf_free*` proof must exclude.

**Fix:** in the stubs, call `__CPROVER_deallocate(p)` in `free` after recording it, and on the old block in `realloc`
after `__CPROVER_array_replace` (`review/model_review.h`). With that model both mutants fail with "deallocated
dynamic object". The unmutated code still proves.

### F2 (high): the empty strbuf (length == 0) is assumed away in three harnesses
`h_free_to_string`, `h_append_string` and `h_helpers` pick an "earlier byte" with
`__CPROVER_assume(k < s->length)`. That makes `length == 0` unsatisfiable: probes `c_free_to_string`, `c_append_string`
and `c_helpers` report `L == 0` as unreachable.

The empty strbuf is the most common state (straight after `strbuf_init` or `strbuf_reset`), and the
CLAIM's "proved" rows for `free_to_string`, `string`, `ensure_null`, `append_*` and `ensure_empty_length` silently skip it.

Survivors:
- `fts-len-skip-empty`: `*len` is not written for an empty string.
- `h-string-len-skip-empty`: the same bug in `strbuf_string`.

`h-ensure-null-skip-empty` is caught only by luck, through `h_init`.

**Fix:** `assume(L == 0 ? k == 0 : k < L)` and guard the `buf[k] == ck` checks with `L != 0` (`any_k` in
`review/harness_review.c`).

### F3 (high for the "every input" wording): size bounds hide 32-bit truncation
`h_helpers` assumes `size <= 16` and `h_append_string` assumes `size <= 8`. Neither bound is needed for the
loop-free helpers. Probe `c_helpers` shows that room above 2^32 is unreachable.

This hides the bug class this repo has found most often (AGENTS.md: "`(int)len` on sizes is the most common bug").
Survivors:
- `h-empty-length-trunc`: `(unsigned)` in `strbuf_empty_length`.
- `h-length-trunc`: `(unsigned)` in `strbuf_length`, which lua_cjson uses to save and restore key-buffer positions.

The CLAIM marks all of these helpers "proved" without saying they are proved only for buffers of at most 16 bytes, and
`append_mem` only for `len <= 6`.

**Fix:** use any size up to `MAX_OBJ` (which needs `--unwindset calculate_new_size.0:66`, since growth may now
double many times) and state the remaining bounds (`append_mem` `n <= 6`, `append_string` `n <= 5`) in CLAIM.md. The
strengthened `r_helpers` proves in about 300 s per signedness.

### F4 (medium): an undocumented precondition on `strbuf_ensure_empty_length` (and so on `append_mem`)
`s->length + len` can wrap. `strbuf_resize` then shrinks the buffer (or dies with "BUG"), and the caller writes `len`
bytes past the block. Probe `q_ensure_wrap` (unbounded `len`) fails.

The harness bound `len <= 16` hides this. It is unreachable from lua_cjson in practice:
- `len * 6` in `json_append_string` would need a string of 2^61 bytes, and `len * 6` would wrap first.
- The other sizes are small constants.

The CLAIM must still list the precondition `len <= SIZE_MAX - length - 1`. `r_helpers` proves the helper for every
`len` under it.

### F5 (medium): `debug != 0` is assumed away for `strbuf_resize`, `strbuf_free` and `strbuf_free_to_string`
`any_strbuf` sets `debug = 0`, so the `debug > 1` branch of `strbuf_resize` is never explored (probe `c_resize`).
Survivor `resize-debug-branch` corrupts `length` only when `debug > 1`.

CLAIM.md does disclose "debug == 0 except in h_debug_stats", but nothing requires that restriction. The branch costs
nothing to verify.

`h_debug_stats` also checks only the struct fields, not the buffer. A debug-only write into `buf` would be caught only
indirectly: `debug-clobbers-buffer` was caught through a NULL dereference in `h_free`, not by the `debug_stats` spec.

**Fix:** use `debug = nondet_int()` in the resize, free and free_to_string harnesses, and check a buffer byte in `h_debug_stats`. Both are in
`harness_review.c`.

### F6 (low): the `reallocs < INT32_MAX / 2` precondition and its justification
The precondition is real: `q_reallocs_max` (`reallocs = INT_MAX`) fails with signed overflow in `reallocs++`. CLAIM.md
justifies it with "each resize needs a larger buffer". That is false for the public API:
- `q_resize_no_growth` proves that `strbuf_resize(s, s->size - 1)` keeps the size and still counts a realloc.
- Shrinking calls (`strbuf_resize(s, small)`) count as well.

It is true for the callers in strbuf.c, strbuf.h and lua_cjson.c: every resize there comes from `ensure_empty_length`
or `append_string` and at least doubles, so at most about 51 resizes fit in 2^50 bytes, even across `strbuf_reset`.

The exact precondition differs per function:
- `strbuf_resize` needs `reallocs < INT_MAX`. `r_resize` proves it under that.
- `strbuf_append_string` needs headroom for several resizes per call. One call made two resizes in `c_append_string`,
  and with `reallocs = INT_MAX - 1` it overflows.

**Fix:** reword CLAIM.md to state `reallocs < INT_MAX` for `strbuf_resize`, with the caller-based argument above. It is
an upstream wart (an `int` counter) worth a note in the finding.

### F7 (low): `strbuf_allocated` is never tested with `buf == NULL`
`any_strbuf` always allocates `buf`, so `c_helpers` shows `buf == NULL` is unreachable, and `h-allocated-true`
(`return 1;`) survives. lua_cjson relies on this function to tell a freed strbuf from a live one.

**Fix:** set `s->buf = NULL` on a nondeterministic branch for that helper (`r_helpers`, `which == 1`).

### F8 (medium, claim text): unbacked statements in CLAIM.md and the finding
- CLAIM.md says "Frama-C WP for the unbounded loop … 48/49 goals". The harness comment says "The unbounded proof is in
  ../wp". **No `wp/` directory exists** in `libraries/neovim/cjson_strbuf/` or anywhere else in the repo, so that
  statement cannot be checked. Either add it or delete the sentence.
- The finding ends with "Proved for every string in `../cjson_strbuf/`". That contradicts CLAIM.md, where
  `strbuf_append_string` is OPEN and CBMC covers strings of at most 5 bytes into buffers of at most 8 bytes. Correct
  the finding.
- `strbuf_set_length` has no harness at all, so `h-set-length-off` survives. Its OPEN status is right. `r_helpers`
  (`which == 13`) proves it for `0 <= len < size`, which is the range lua_cjson's callers use (they restore a saved
  `strbuf_length`). Only the `int` parameter and the negative values stay open.

### F9 (note): the spec is partly a transcription of the code
The `calculate_new_size` contract ("exact when `len + 1 >= SIZE_MAX / 2`", "shrink exactly") restates the code. The
comments do say "shrink … exactly" and "Exponential sizing", so this is acceptable, but CLAIM.md should say that the
threshold is taken from the code. Things that hold and are worth keeping:
- The doubling postcondition ("size times a power of two" and "least such") is sharp: it caught 1.5× growth, an extra
  doubling and a moved threshold.
- `q_cns_wide` proves `calculate_new_size` for every `size >= 1`, not only `size <= 2^50` (probe `c_cns`).
- `r_calculate_new_size` adopts that.

### Things checked and found fine
- `--unwinding-assertions` is passed on every run. The unwind bounds (66 for the doubling loop, 8 for the copy loops) are
  enough: they pass with unwinding assertions.
- Both char signednesses are covered: `${sign#signed}` expands to nothing (x86_64, so signed) and to `--unsigned-char`.
  `--arch x86_64` is pinned.
- The sha256 pins in run_cbmc.sh match the fixed `strbuf.c` and `strbuf.h`, and the code under test is included verbatim.
- `malloc` and `realloc` may fail on every call, and the sticky `alloc_failed` flag is sound here: the code dies at the
  first failure, so the flag never excuses a later die. Fresh blocks are uninitialised and have exact sizes.
- `die` gets a real `abort` that stops the path, and `die_ok` limits dying to the documented cases.
- The failure paths of every postcondition are reachable (`--cover assertion`).

## Mutants (`mutants.toml`, `mutants_result.tsv`)
| id | function | expected | original harnesses | strengthened (review/) |
|---|---|---|---|---|
| die-returns | die | caught | caught h_die | |
| init-default-size, init-no-nul-room, init-len1-default, init-malloc-len | strbuf_init | caught | caught h_init "size" | |
| init-reallocs-kept / init-no-nul | strbuf_init | caught | caught h_init | |
| init-overflow-le | strbuf_init | equivalent | survived | survived |
| new-not-dynamic, new-sizeof-pointer | strbuf_new | caught | caught h_new | |
| debug-inverted | debug_stats | equivalent (stderr only) | survived | survived |
| debug-clobbers-reallocs | debug_stats | caught | caught h_debug_stats | |
| debug-clobbers-buffer | debug_stats | caught | caught (h_free NULL deref, indirect) | |
| free-no-clear, free-dynamic-leak | strbuf_free | caught | caught h_free | |
| **free-uaf-order** | strbuf_free | caught | **survived (F1)** | caught r_free: deallocated object |
| fts-no-nul, fts-frees-buf | strbuf_free_to_string | caught | caught | |
| **fts-uaf-return** | strbuf_free_to_string | caught | **survived (F1)** | caught r_free_to_string |
| **fts-len-skip-empty** | strbuf_free_to_string | caught | **survived (F2)** | caught r_free_to_string |
| cns-no-nul-room, cns-shrink-off-by-one, cns-threshold, cns-growth-factor, cns-loop-le | calculate_new_size | caught | caught h_calculate_new_size | |
| cns-len-lt1, cns-shrink-ge, cns-dead-check | calculate_new_size | equivalent | survived | survived |
| resize-no-reallocs, resize-realloc-short, resize-no-oom-check | strbuf_resize | caught | caught h_resize | |
| **resize-debug-branch** | strbuf_resize | caught | **survived (F5)** | caught r_resize |
| **append-int-index** (= upstream) | strbuf_append_string | caught | **survived** | survived: needs an unbounded proof |
| append-resize-short, append-no-space-dec | strbuf_append_string | caught | caught h_append_string | |
| append-space-stale, append-space-early | strbuf_append_string | equivalent | survived | survived |
| append-truncated-room | strbuf_append_string | equivalent | survived | flagged by --conversion-check only (explicit narrowing cast on room ≥ 2^32), not by a semantic assertion |
| h-reset-noop, h-empty-length-no-nul, h-ensure-ge, h-empty-ptr, h-extend-off | helpers | caught | caught h_helpers | |
| h-append-char-no-room, h-append-char-unsafe-noinc, h-append-mem-short-room, h-append-mem-unsafe-offset | helpers | caught | caught h_helpers | |
| h-ensure-null-skip-empty | strbuf_ensure_null | caught | caught (via h_init) | |
| **h-allocated-true** | strbuf_allocated | caught | **survived (F7)** | caught r_helpers WHICH=1 |
| **h-empty-length-trunc** | strbuf_empty_length | caught | **survived (F3)** | caught r_helpers WHICH=2 |
| **h-length-trunc** | strbuf_length | caught | **survived (F3)** | caught r_helpers WHICH=4 |
| **h-string-len-skip-empty** | strbuf_string | caught | **survived (F2)** | caught r_helpers WHICH=5 |
| **h-set-length-off** | strbuf_set_length | caught | **survived (no harness, F8)** | caught r_helpers WHICH=13 |

`run_mutants.py` exits 1 because of the 10 bold rows. That is the intended verdict until the harness is fixed.

### On `append-int-index`
This mutant is the upstream code. The bounded harness cannot distinguish `int i` from `size_t i` below 2^31
bytes. The CLAIM row (OPEN) is therefore honest. Either of these would close it:
1. Finish and commit the WP proof.
2. Use a CBMC loop contract (`goto-instrument --apply-loop-contracts` with an invariant
   `i == s->length - L0 && s->length < s->size && space == s->size - s->length - 1`) over a
   symbolic string with no size bound. `--signed-overflow-check` would then flag `i++` at `INT_MAX`.

## Required before admission
1. Model frees and reallocs as deallocating (F1).
2. Allow `length == 0` (F2).
3. Drop the `size <= 8` and `size <= 16` bounds, or state them in CLAIM.md as limits of the proof (F3).
4. List the `ensure_empty_length` / `append_mem` precondition (F4).
5. Explore `debug != 0` (F5).
6. Fix the `reallocs` justification (F6).
7. Cover `buf == NULL` (F7).
8. Remove or commit the WP claim, and correct the finding's last line (F8).

`review/harness_review.c` with `review/model_review.h` implements 1, 2, 3, 5, 6 (for resize) and 7, plus
`set_length` on `0 <= len < size`, and proves on the fixed code. Adopting it into `cbmc/` (same names `h_*`) would
make every survivor except `append-int-index` and the equivalents fail.

## Files added by this review
- `REVIEW.md`, `mutants.toml`, `run_mutants.py`, `mutants_result.tsv`
- `review/probes.c` and `review/probes.sh`: cover and precondition probes, `bash review/probes.sh <dir with strbuf.c/h>`.
- `review/harness_review.c`, `review/model_review.h` and `review/run_review.sh`: the strengthened harnesses.
