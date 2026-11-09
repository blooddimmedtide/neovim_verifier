# Claim card: Neovim hashtab.c (in progress, not verified)

Frama-C WP, upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd, `wp/run_wp.sh` (verbatim
sha-pinned text plus ACSL comments; 64-bit facts checked by `wp/bvlemmas.py`, 23/23).

Status 2026-11-09 (every run now with `-wp-smoke-tests`; earlier counts were taken without them
and are being rerun):

| function | status |
|---|---|
| hash_init, hash_clear, hash_lock, hash_debug_results, _hash_key_removed | proved |
| hash_hash, hash_hash_len, hash_find, hash_find_len, hash_lookup (with termination) | proved |
| hash_clear_all | proved |
| hash_add, hash_add_item, hash_remove, hash_unlock | proved against hash_may_resize's contract |
| hash_may_resize | 250 / 269 goals, smoke tests 77 / 77; open: the outer move loop's invariants, the kept/resized posts (Qed takes ~60 s per goal: split into ghost helpers) |

Not yet done: the CBMC equivalence checks for the tool patches (`wp/tool_patches.py`), the
differential test, the review pass with planted bugs.

Findings so far (preconditions record them; write-ups pending):
- `ht_changed` is a signed `int` incremented on every add/remove/resize: undefined behaviour
  after 2^31 changes.
- A locked table is never resized: adding to a locked table with one never-used item left
  fills it, after which hash_lookup never stops for an absent key.
