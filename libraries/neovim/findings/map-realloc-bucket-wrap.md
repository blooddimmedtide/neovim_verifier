# map.c: hash index wraps to 0 buckets past 2^31 buckets (heap overflow)

Found by the Frama-C WP proof of `mh_realloc` (upstream 7b87ce8): the proof needs
`n_min_buckets <= 2^31`, and `mh_put_*` breaks that.

- `mh_put_*` grows the index with `mh_realloc(h, h->n_buckets + 1)` once
  `size >= 0.9 * upper_bound`. With `n_buckets == 2^31` (upper bound 1,653,562,573)
  that is about 1.49e9 live keys.
- `mh_realloc` then rounds 2^31 + 1 up with `roundup32` on a `uint32_t`: the result
  2^32 wraps to **0**. It calls `xcalloc(0, 4)`, stores `n_buckets = 0` and
  `upper_bound = 0`.
- `mh_rehash_*` runs right after, and `mh_find_bucket_*` computes
  `mask = n_buckets - 1 = 0xFFFFFFFF`, so it reads and writes `h->hash[i]` for any
  32-bit `i` in a 0-byte block: heap out-of-bounds read and write.

Reproducer: `map/repro/realloc_wrap.c` runs the verbatim `mh_realloc` on 2^31 + 1 and
prints `xcalloc(0, 4)` and `n_buckets=0 ... mask=4294967295` (exit 1). The full path
needs ~1.49e9 keys in one Map/Set (tens of GB of RAM), so it was not run end to end here.

A second wrap sits behind it: `keys_capacity = MAX(keys_capacity * 2, 8)` is `uint32_t`
arithmetic, so at `keys_capacity == 2^31` it becomes 8 and `set->keys[pos]` is written
past the new 32-byte block. It is only reached if the bucket wrap above is fixed
without also capping the key count.

Fix: verified_neovim branch claude/project-thread-ik9odv, commit 9821c98: `mh_realloc`
calls abort() when asked for more than 2^31 buckets. With the bucket count capped, the
keys_capacity wrap is unreachable (the table aborts at ~1.49e9 keys, before keys_capacity
would need to pass 2^31). Proof: map/wp/map_realloc_fixed.c, 59/62 goals (see STATUS.md).

Status: upstream `mh_realloc` is proved for `n_min_buckets <= 2^31` only (56/59); the fixed
version is written and 59/62 proved. Draft upstream issue: `/mnt/project-files/neovim-verify/upstream/issue-map-bucket-wrap.md`.
