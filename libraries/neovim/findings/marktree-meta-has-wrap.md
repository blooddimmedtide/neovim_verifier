# marktree.c `meta_has` can miss marks when selected counts add up to 2^32

Pinned upstream: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd, `src/nvim/marktree.c:485`.

`meta_has(meta_count, meta_filter)` decides whether a marktree node (with its subtree) holds any
mark of the kinds the filter selects. Upstream adds the selected counts in a `uint32_t` and tests
the sum:

```c
uint32_t count = 0;
for (int m = 0; m < kMTMetaCount; m++) {
  count += meta_count[m] & meta_filter[m];
}
return count > 0;
```

With a filter of the documented shape (`kMTFilterSelect` or 0 per kind) that selects two kinds,
such as `sign_filter` in decoration.c (SignText and SignHL), counts of 2^31 and 2^31 sum to 2^32,
which wraps to 0. `meta_has` then returns false and `marktree_itr_step_out_filter` /
`marktree_itr_next_filter` skip a subtree that holds matching marks.

CBMC finds this counterexample (`cbmc/run_cbmc.sh <upstream tree> upstream`, `check_meta_has`,
also with `-D DOC_FILTER`).

**Reachability.** It needs at least 2^31 sign marks under one node, which needs far more memory than
any real session has (every mark is a 40-byte key in the tree plus an id2node entry). So this is a
latent bug, not one a user can hit today; it matters only if the counter type or filters change.

**Fix** (verified_neovim branch `claude/project-thread-aeqr1o`, commit 5ee8dd2): test each kind on
its own and return true at the first selected nonzero count. Proved with CBMC for every count and
filter value (`cbmc/run_cbmc.sh <fixed tree> fixed`, 8/8 runs pass).

Upstream issue draft: /mnt/project-files/neovim-verify/upstream/issue-marktree-meta-has-wrap.md (not filed).
