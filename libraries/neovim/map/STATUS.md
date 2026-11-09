# map.c / kvec.h verification status (stopped 2026-11-09 ~08:40 UTC, usage deadline)

Upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. Tool: Frama-C 33 WP
(`-wp-rte -wp-model Typed+Cast`, Z3 5.1 + CVC5 1.4), one run per function: `bash wp/run.sh`.
Verbatim check: `python3 -I wp/check_strip.py <neovim tree>` (strip `/*@ */`, sha256 pins).
Nothing here is reviewed yet (no planted-bug run, no independent review): all rows are
at most `candidate`.

map.c expands to about 108 C functions: 10 helpers in map.c, 5 key functions x 10 key
types (map_key_impl.c.h), 3 value functions x 16 key/value pairs (map_value_impl.c.h).

## Proved (int-key instance, full goal count)

| Function | Goals | What is proved |
|---|---|---|
| mh_realloc | 47/47 | for `n_min_buckets <= 2^31`: new zeroed index, `n_buckets` a power of two, `>= max(16, n_min)`, `<= 2^31`; counters reset. Uses `roundup_lemma` (Z3, `wp/lemmas.smt2`). Larger inputs: finding below. |
| mh_clear | 26/26 | all buckets 0 and size/n_occupied/n_keys 0 when allocated; nothing changed otherwise |
| mh_get_int | 15/15 | result is TOMBSTONE or an index `< n_keys` whose key equals `key` (relies on mh_find_bucket_int's contract, incl. its open termination goal) |
| map_ref_int_ptr_t | 15/15 | NULL, or `&values[k]` with `keys[k] == key`, and `*key_alloc` set to `&keys[k]` |

## Partly proved

| Function | Goals | Open |
|---|---|---|
| mh_find_bucket_int | 46/49 | memory safety, all postconditions and the loop invariants are proved. Open: termination. The variant `2n-2-step` is in place; the 3 asserts that relate `i` to `last + step(step+1)/2 mod n` time out (nonlinear `%`); helper lemmas `mod_add`, `mod_wrap` in map_int.c also time out (`mod_mul` proved). `mask_lemma` is Z3-checked (`wp/lemmas_mask.smt2`). Also not specified yet: *completeness* (a free slot returned means the key is absent), which needs a table-wide probe-chain invariant. |

## Not started (still unverified)

- map.c helpers: hash_cstr_t, hash_path_t, equal_path_t, hash_HlEntry, equal_HlEntry,
  hash_ColorKey, equal_ColorKey, pmap_del2.
- int keys: mh_rehash_int, mh_put_int, mh_delete_int; map_put_ref_int_ptr_t,
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

1. Prove the 3 asserts in mh_find_bucket_int: replace `%` with an explicit ghost quotient
   (`last + T(step) == q * n + i`) so the step is linear, or check them as bit-vector lemmas.
2. Spec and prove mh_rehash_int, mh_put_int, mh_delete_int, then map_put_ref/map_del.
3. Write the fix for the bucket wrap on a verified_neovim branch and prove it.
4. Generalise build to every key type (the bodies are identical; only hash_/equal_ differ).
5. kvec.h.
