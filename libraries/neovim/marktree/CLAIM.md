---
entry: neovim/src/nvim/marktree.c (leaf functions: position algebra, key order, node search, intersect arrays, meta counters, iterator helpers)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-aeqr1o, commit 5ee8dd2, meta_has fix)
toolchain: Frama-C 33.0 (Arsenic) WP (Typed+Cast, RTE), Z3 + CVC5; CBMC 6.11.0 (n/a)
strength: candidate   # becomes full-correctness after the owner signs off the spec
platform: x86_64; char signed and unsigned (CBMC); the WP functions use no char
---

# Claim card: Neovim marktree.c leaf functions (15 of 82 functions)

## What is proved, for every input that meets the stated preconditions

Positions are (row, col) pairs; "valid position" means 0 <= row, col <= INT_MAX.

| Function | Tool | Property |
|---|---|---|
| `pos_leq(a, b)` | WP | true iff a <= b in (row, col) order |
| `pos_less(a, b)` | WP | true iff a < b |
| `relative(base, v)` | WP | for valid base <= v: v becomes its offset from base (row 0 = same row, col difference; else row difference, same col); the upstream `assert(pos_leq(base, *val))` is proved to hold; result is a valid position |
| `unrelative(base, v)` | WP | v becomes the absolute position of offset v from base, when that position is valid |
| `compose(base, v)` | WP | base becomes unrelative(base, v), same precondition |
| lemmas | WP | unrelative(base, relative(base, v)) == v; relative keeps the order of positions at or after base. These are the invariants the B-tree's relative storage needs |
| `key_cmp(a, b)` | WP | -1/0/1 for the order (row, col, flags & (RIGHT_GRAVITY,END,REAL,LAST)); proved antisymmetric and transitive (lemmas) |
| `marktree_getp_aux(x, k, match)` | WP | for a node with 0..19 keys in key order: returns r in -1 .. n-1 with keys[0..r] <= k, keys[0..r-1] < k; if keys[r] != k (or r = -1) every later key is > k; \*match (when given) is true iff keys[r] == k. A match is the first equal key |
| `intersection_has(x, id)` | WP | for an ascending array: true iff id is in it |
| `intersect_item_pos(x, id)` | WP | for an ascending array: the lower bound (first index with item >= id) |
| `marktree_itr_node_done(itr)` | WP | true iff no node or at the node's last key |
| `marktree_itr_pos(itr)` | WP | the absolute position of the current key (unrelative of the iterator base) |
| `itr_eq(a, b)` | WP | true iff the two iterators address the same key; for the same or non-overlapping nodes, iff same node and index |
| `meta_describe_key_inc(meta, k)` | CBMC | adds 1 (mod 2^32) to each kind the key's decoration flags name, unless the key is an end key or invalid |
| `meta_describe_key(meta, k)` | CBMC | meta becomes exactly the key's own counts |
| `meta_has(count, filter)` (fixed fork) | CBMC | true iff some kind has count & filter != 0, for every count and filter |
| `meta_has` (upstream) | CBMC | fails: counterexample with two selected counts adding up to 2^32 (see Finding); not proved |

Header helpers `mt_end` and `mt_invalid` (marktree.h) are also proved (WP).

## Preconditions (each is a B-tree invariant or a documented contract)

- Valid positions; for unrelative/compose/itr_pos, the absolute position is valid (true of every key in a buffer).
- relative: base <= v (upstream asserts it).
- getp_aux: node holds 0 .. 2*MT_BRANCH_FACTOR-1 keys in key order (marktree_check_node checks this).
- intersect arrays ascending (doc comment of intersect_item_pos).
- itr helpers: the iterator's node is valid and its index is a key slot.

## Finding

`meta_has` sums the selected counts in a uint32_t; two selected kinds with 2^31 marks each wrap the sum to 0
and the filtered iterators skip marks. Not reachable with today's memory (needs over 2^31 marks), so latent.
Fixed and proved: findings/marktree-meta-has-wrap.md. Doc-only: findings/marktree-getp-doc.md.

## How the code is taken

build.py copies each function's exact text (sha256 pinned per function, upstream and fixed), inserts ACSL in
comments only, and checks that removing the comments gives the pinned text back. Types and macros in
stubs/vp_marktree.h are checked line by line against the pinned headers; DecorInlineData is opaque (no proved
function reads it). The upstream `assert` becomes a call whose precondition is the asserted condition.

## Reproduce

    bash marktree/wp/run_wp.sh <neovim tree> upstream|fixed 20
    bash marktree/cbmc/run_cbmc.sh <neovim tree> upstream|fixed   # upstream meta_has fails by design (the finding)

## Checks run (2026-11-09)

- WP, upstream and fixed trees: every goal proved, with `-wp-smoke-tests` (no contradictory preconditions found).
- CBMC: meta_* functions, both char signednesses, fixed tree 8/8; upstream meta_has fails (the finding).
- Independent review: REVIEW.md, 20/20 non-equivalent planted bugs caught (mutants.toml).
  Review finding 1 (an annotation holding `*/ ... /*@` could smuggle code past the strip check) is fixed: build.py
  rejects comment tokens in every contract, annotation and LOGIC. Finding 2 is fixed too: each copied type is now
  checked as a whole block, in order (a swapped field fails the build). Open: finding 3 (DecorInlineData opaque, MTNode without `s[]`; no proved function depends
  on layout). The meta_* contracts in contracts.py are not run by WP; their proof is the CBMC harness.
