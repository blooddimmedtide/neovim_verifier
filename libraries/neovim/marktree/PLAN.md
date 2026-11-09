# mark.c + marktree.c (claim)

Claimed by the "Verify Neovim marks code" thread, 2026-11-09. Pinned upstream: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd.
Tool: Frama-C WP (Typed+Cast, RTE, Z3/CVC5), tooling copied from garray/wp and hashtab/wp.

Inventory: mark.c 56 functions, marktree.c 82 functions (138 total). None is verified yet; this file lists progress.

## Order
1. marktree.c position algebra: pos_leq, pos_less, relative, unrelative, compose, key_cmp
   (key invariant: unrelative(base, relative(base, p)) == p, and order is preserved).
2. marktree.c intersection arrays: intersection_has, intersect_item_pos (sorted-array search).
3. marktree.c meta counters: meta_describe_key_inc, meta_describe_key, meta_has.
4. B-tree structural invariants (marktree_check_node as the spec), then insert/delete/split/merge.
5. mark.c.
