# map.c / kvec.h verification status (stopped 2026-11-09 ~08:25 UTC, usage deadline)

Upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. Tool: Frama-C 33 WP
(`-wp-rte -wp-model Typed+Cast`, Z3 5.1 + CVC5 1.4), one run per function: `bash wp/run.sh`.
Verbatim check: `python3 -I wp/check_strip.py <neovim tree>` (strip `/*@ */`, sha256 pins).
Nothing here is reviewed yet (no planted-bug run, no independent review): all rows are
at most `candidate`.

map.c expands to about 108 C functions: 10 helpers in map.c, 5 key functions x 10 key
types (map_key_impl.c.h), 3 value functions x 16 key/value pairs (map_value_impl.c.h).

All runs use `-wp-smoke-tests` (checks that no contract makes code unreachable). The
first allocation stub (xcalloc with a "for all live pointers" clause, like garray's) was
contradictory: smoke tests showed dead code after the call, so the earlier 47/47 for
mh_realloc was vacuous. The stub now takes a ghost "avoid" pointer instead.

## Proved (int-key instance, full goal count, smoke tests clean)

Goal counts include smoke tests (last run: `NVIM_TREE=<upstream tree> SKIP_BV=1 bash wp/run.sh 30`, 2026-11-09 08:50 UTC, all 6 runs complete).

| Function | Goals | What is proved |
|---|---|---|
| mh_find_bucket_int | 65/65 | memory safety, **termination** (quadratic probing over a power-of-two table returns to its start after 2n-1 steps: variant `2n-2-step`, ghost `probe_lemma` checked by Z3 for every n = 2^k in `wp/lemmas_probe.smt2`, 96 unsat), and: with `put` the result is a slot `< n_buckets`; a returned used slot holds `key`; without `put` the result is TOMBSTONE or a slot holding `key`. |
| mh_realloc (upstream) | 59/59 | fully proved **for `n_min_buckets <= 2^31` only**: frees the old index, new zeroed index, `n_buckets` a power of two in `[max(16, n_min), 2^31]`, counters reset, upper_bound cast in range. Larger inputs are the finding below; the fixed version needs no precondition. |
| mh_rehash_int | 51/51 | memory safety, termination, no tombstones remain, every key j gets a slot holding j + 1 (ghost witness array `vp_slot`), only the index, n_occupied and size change. |
| mh_clear | 32/32 | all buckets 0 and size/n_occupied/n_keys 0 when allocated; nothing changed otherwise |
| mh_get_int | 20/20 | result is TOMBSTONE or an index `< n_keys` whose key equals `key` |
| map_ref_int_ptr_t | 20/20 | NULL, or `&values[k]` with `keys[k] == key`, and `*key_alloc` set to `&keys[k]` |

## Partly proved

None right now.

Not specified yet for any function: *completeness* of lookup (a free slot returned means the
key is absent), which needs a table-wide probe-chain invariant; and "never calls abort()"
(all abort() exits are allowed by the contracts, as `exits \true`).

## Not started (still unverified)

- map.c helpers: hash_cstr_t, hash_path_t, equal_path_t, hash_HlEntry, equal_HlEntry,
  hash_ColorKey, equal_ColorKey, pmap_del2.
- int keys: mh_put_int, mh_delete_int (needs a weaker find_bucket precondition: it is called after n_keys is decremented); map_put_ref_int_ptr_t,
  map_del_int_ptr_t; the int/String, int/StcClick, int/StcClicks value instances.
- All 5 key functions for ptr_t, cstr_t, path_t, String, uint32_t, uint64_t, int64_t,
  HlEntry, ColorKey (45 functions), and their value instances (map_ref/map_put_ref/map_del
  for ptr_t/ptr_t, cstr_t/ptr_t, cstr_t/int, String/int, uint32_t/ptr_t,
  uint32_t/uint32_t, uint64_t/ptr_t, uint64_t/int, uint64_t/MTDamagePair,
  int64_t/ptr_t, int64_t/int64_t, ColorKey/ColorItem).
- kvec.h: `_memcpy_free` and the `kv_*` macros (kv_resize, kv_ensure_space,
  kv_concat_len, kv_pushp, kv_a, kv_shift, kv_copy, kvi_*). Not started. Noted while
  reading: `kv_resize` multiplies `sizeof * capacity` unchecked and `kv_roundup32` only
  ORs up to `>> 16` on a `size_t` (the comment in kv_concat_len says this is intended);
  both need a proof or a finding.

## Fix (written and proved)

`verified_neovim` branch `claude/project-thread-ik9odv`, commit 9821c98: `mh_realloc` calls
`abort()` when more than 2^31 buckets are asked for, instead of wrapping to 0. Proof file
`wp/map_realloc_fixed.c` (verbatim check: `python3 -I wp/check_strip.py <fork tree> fixed`):
**62/62 goals, 11/11 smoke tests, no size precondition**. The zero-fill goals closed with a
frame assertion: ghost label `VpL` before the header writes and
`assert \forall i < n: h->hash[i] == \at(h->hash[i], VpL)` at the end (gives the SMT
solver a trigger term). No fork PR opened yet; not reviewed.

Note: `check_strip.py` without `fixed` needs a tree at the pinned upstream commit
(the fork checkout on the fix branch differs in mh_realloc).

## Finding

- `findings/map-realloc-bucket-wrap.md`: past 2^31 buckets (~1.49e9 keys) `mh_realloc`
  wraps to 0 buckets and the rehash writes out of bounds. Reproducer `repro/realloc_wrap.c`.
  Fix: fork commit 9821c98 (62/62 proved). Draft upstream issue (not filed):
  /mnt/project-files/neovim-verify/upstream/issue-map-bucket-wrap.md.

## Trusted (would go in CLAIM.md)

- `wp/stubs/vp_map.h`: contracts of xfree, xcalloc (never NULL, zeroed), xrealloc,
  memset (zero fill of uint32 words), abort (never returns).
- Bodiless ghost lemmas `roundup_lemma`, `mask_lemma`, each checked by Z3 bit-vectors.
- `#define set vset` in the prelude: `set` is an ACSL keyword, so the preprocessor renames
  the identifier in C and ACSL alike (pure alpha-renaming).

## Next steps

1. Run the planted-bug suite and an independent review on the proved functions.
2. Spec and prove mh_put_int (needs `n_buckets < 2^31`: the finding) and mh_delete_int,
   then map_put_ref/map_del.
3. Open a fork PR for 9821c98 into `verified`; planted-bug run and review.
4. Generalise to every key type (the bodies are identical; only hash_/equal_ differ).
5. Lookup completeness and no-abort, then the 8 map.c hash/equal helpers and pmap_del2.
6. kvec.h.
