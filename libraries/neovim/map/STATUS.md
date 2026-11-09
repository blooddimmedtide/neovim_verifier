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

| Function | Goals | What is proved |
|---|---|---|
| mh_find_bucket_int | 50/50 (+15 smoke) | memory safety, **termination** (quadratic probing over a power-of-two table returns to its start after 2n-1 steps: variant `2n-2-step`, ghost `probe_lemma` checked by Z3 for every n = 2^k in `wp/lemmas_probe.smt2`, 96 unsat), and: with `put` the result is a slot `< n_buckets`; a returned used slot holds `key`; without `put` the result is TOMBSTONE or a slot holding `key`. |
| mh_clear | 26/26 | all buckets 0 and size/n_occupied/n_keys 0 when allocated; nothing changed otherwise |
| mh_get_int | 15/15 | result is TOMBSTONE or an index `< n_keys` whose key equals `key` |
| map_ref_int_ptr_t | 15/15 | NULL, or `&values[k]` with `keys[k] == key`, and `*key_alloc` set to `&keys[k]` |

## Partly proved

| Function | Goals | Open |
|---|---|---|
| mh_realloc | 56/59 | proved: frees the old index, `n_buckets` is a power of two in `[max(16, n_min), 2^31]` for `n_min <= 2^31` (`roundup_lemma`, Z3 `wp/lemmas.smt2`), counters reset, upper_bound cast in range, fresh zeroed block. Open: that the zeroes survive the three header-field writes after the call (2 asserts + 1 ensures; WP does not use `\base_addr` disequality through the `(char *)h` cast). Fix idea: give xcalloc's ghost avoid argument type `MapHash *`. Larger inputs: finding below. |
| mh_rehash_int | 38/41 | proved: memory safety, termination, no tombstones remain, every key j gets a slot holding j + 1 (ghost witness array `vp_slot`). Open: the last ensures and the function's two assigns goals (time out). |

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

## Finding

- `findings/map-realloc-bucket-wrap.md`: past 2^31 buckets (~1.49e9 keys) `mh_realloc`
  wraps to 0 buckets and the rehash writes out of bounds. Reproducer `repro/realloc_wrap.c`.
  Fix not written or proved yet. Draft upstream issue (not filed):
  /mnt/project-files/neovim-verify/upstream/issue-map-bucket-wrap.md.

## Trusted (would go in CLAIM.md)

- `wp/stubs/vp_map.h`: contracts of xfree, xcalloc (never NULL, zeroed), xrealloc,
  memset (zero fill of uint32 words), abort (never returns).
- Bodiless ghost lemmas `roundup_lemma`, `mask_lemma`, each checked by Z3 bit-vectors.
- `#define set vset` in the prelude: `set` is an ACSL keyword, so the preprocessor renames
  the identifier in C and ACSL alike (pure alpha-renaming).

## Next steps

1. Close mh_realloc's 3 goals (typed avoid pointer) and mh_rehash_int's 3 goals.
2. Spec and prove mh_put_int (needs `n_buckets < 2^31`: the finding) and mh_delete_int,
   then map_put_ref/map_del.
3. Write the fix for the bucket wrap on a verified_neovim branch and prove it.
4. Generalise to every key type (the bodies are identical; only hash_/equal_ differ).
5. Lookup completeness and no-abort, then the 8 map.c hash/equal helpers and pmap_del2.
6. kvec.h.
