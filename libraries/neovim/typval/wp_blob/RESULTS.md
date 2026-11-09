# typval.c blob functions: Frama-C WP results (upstream 7b87ce8)

Run: `PATH=$HOME/.vpipe/bin:$PATH bash libraries/neovim/typval/wp_blob/run_wp.sh <neovim checkout at 7b87ce8> 15`
(Frama-C 33.0, Why3 1.8.2, Z3 + CVC5, `-wp-model Typed+Cast -wp-rte -wp-smoke-tests
-warn-signed-overflow -warn-signed-downcast`, x86_64). Exit 0 = every goal proved.
Run on 2026-11-09 08:08 UTC: all 14 functions, every goal proved, every smoke test passed
(no dead code / contradictory callee contracts).

| Function | File | Goals | Notes |
|---|---|---|---|
| tv_blob_set_ret | typval.h | 14/14 | |
| tv_blob_len | typval.h | 9/9 | |
| tv_blob_get | typval.h | 7/7 | |
| tv_blob_set | typval.h | 7/7 | |
| tv_blob_alloc | typval.c | 21/21 | |
| tv_blob_free | typval.c | 13/13 | |
| tv_blob_unref | typval.c | 30/30 | needs refcount > INT_MIN |
| tv_blob_alloc_ret | typval.c | 21/21 | |
| tv_blob_copy | typval.c | 54/54 | |
| tv_blob_index | typval.c | 52/52 | spec over rettv's blob (the `blob` arg is unused) |
| tv_blob_slice | typval.c | 130/130 | upstream needs `exclusive ==> n2 > INT64_MIN`: FINDINGS.md #1 |
| tv_blob_slice_or_index | typval.c | 36/36 | same precondition |
| tv_blob_set_append | typval.c | 38/38 | needs idx >= 0 (caller-checked) |
| tv_blob_set_range | typval.c | 60/60 | needs a caller-checked range in dest, src data separate from dest data |

Not done: tv_blob_remove, tv_blob2items, the blob parts of tv_equal/tv_copy, f_* blob
builtins (other files). tv_blob_slice's upstream proof is conditional on finding #1;
no fix branch or fixed-code proof yet.

Spec mutants (sanity, 2026-11-09): dropping the INT64_MIN precondition (slice), shifting the
slice contents by one, dropping `0 <= idx` (set_append), and a wrong negative-index result
(index): each makes WP fail (102/103, 102/103, 27/29, 40/41). Not yet a full adversarial review.

## Pieces and build
`build.py` copies each function verbatim from the pinned tree (sha256 in `pins.txt`), puts
contracts on prototypes in the prelude, and inserts loop invariants and ghost call arguments
as `/*@ */` comments; it checks that removing them gives back the pinned text exactly.
Type definitions in the prelude are copied from typval_defs.h (spot-checked lines in CHECKS);
`dictvar_S` and `listitem_S` are truncated (fields never read by these functions).

## Trusted assumptions (unproved callee contracts)
- `xcalloc` (memory.c): non-NULL, zeroed `blob_T`; stated only for `xcalloc(1, sizeof(blob_T))`.
- `xmemdup` (memory.c): non-NULL copy of `len` bytes. `xfree`: live-count bookkeeping only.
- Allocator freshness: WP does not model `allocates`, so "the new block differs from every
  block valid before" is unsound to state (it is contradictory: see below). Instead each
  allocator (and `tv_blob_alloc`, `tv_blob_alloc_ret`, `ga_grow`) takes ghost arguments naming
  live objects, and promises its new block's base differs from each. True of any allocator.
- `ga_init`, `ga_clear`: the contracts proved in libraries/neovim/garray (PR #4).
  `ga_grow`: implied by that proved contract for itemsize 1 (upstream growth fits in an int),
  plus the ghost freshness above for a moved block.
- `tv_clear` (NOT proved; runs the typval_encode walker): changes only `*tv`'s fields and the
  live count, and frees only memory reachable from `*tv`.
- `semsg` / `emsg`: only counted (ghost `vp_msgs`).

## Important for the garray / hashtab proofs
The garray stub `xrealloc` (garray/wp/stubs/vp_garray.h) ensures
`vp_new_or_same{Pre}(\result, p)` = "every pointer valid in Pre whose base differs from p's
has a base different from \result's". Because WP keeps one allocation table, `\result` itself
counts as valid in Pre, so whenever `\result`'s base differs from `p`'s (always when p == NULL)
the postcondition is false. Check: a function calling `xrealloc(NULL, 8)` with that exact
contract proves `//@ assert \false;` (8/8 goals; scratch test v.c). So every WP path through
a fresh or moved xrealloc in garray (ga_grow growing from empty or moving) is proved
vacuously. Running `-wp-smoke-tests` on garray/hashtab should show it; the fix is the
ghost-argument freshness used here.
