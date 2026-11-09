# shada.c — what is verified, and what the rest needs

Pinned upstream `7b87ce822e6fd45a4d9993599c2854afdb0dc4dd`.

## Verified in this session (CBMC, all inputs, signed + unsigned char)
- `vim_be64toh`, `fread_len`, `sd_reader_skip`, `msgpack_read_uint64`, `shada_check_status`
  — the untrusted-byte reading layer. See `CLAIM.md`, proofs in `cbmc/`, review in `cbmc/REVIEW.md`
  (12/12 planted bugs caught).
- Write-back array-size guard arithmetic (`cbmc/harness.c` `h_arrsize_guard`), the fix for the
  finding below. It quantifies over every possible additional-item count, so the counting property
  of the fix is fully established, not just sampled.

## Finding + fix
`findings/shada-additional-data-nitems-wrap.md`: the write-side `arr_size = (uint32)(k +
additional_data_len())` wraps for an entry with ~2^32 additional items. Fix = read-side reject,
verified_neovim#15; guard arithmetic proved. Full-function proof pending (see below).

## The blocker for the rest of the reader
The remaining reader entry points are **not** cleanly verifiable in isolation, and this is a
structural dependency, not a time problem:

- `shada_read_next_item` (the entry parser) calls `unpack_array`, `unpack_integer`,
  `unpack_string`, `unpack_typval`, `unpack_keydict`, `unpack_skip` — all in
  `src/nvim/msgpack_rpc/unpacker.c`. That file is owned and actively changed by the
  msgpack-unpacker / data-structures thread (e.g. verified_neovim#9). Verifying
  `shada_read_next_item` here would either overlap that thread or require treating those callees as
  trusted stubs — i.e. assumptions about unproved code, which the standard forbids
  (no `admit`, no unchecked assume).
- `hmll_init`/`hmll_remove`/`hmll_insert`/`hmll_dealloc` and the `hms_*` merge structures depend on
  the `Map`/khash machinery (`pmap_put_ref`, `pmap_del`, `map_destroy`) and `shada_free_shada_entry`.
- `shada_removable` depends on `p_shada` option parsing and path/home-replace machinery.

## Next step (unblocks shada_read_next_item)
1. The unpacker thread verifies the small decoders `unpack_array`, `unpack_integer`,
   `unpack_string`, `unpack_skip` against a MessagePack-spec reference (they are self-contained over
   `mpack_rtoken`, so each is a bounded CBMC target much like the primitives proved here).
2. Build those proved contracts into a model (`cbmc/unpacker_model.h`) and extend `cbmc/build.py`
   to extract `shada_read_next_item`, then prove: no out-of-bounds read of the item buffer for any
   `length`/content, the `length_u64 > PTRDIFF_MAX` and the new additional-item guards hold, and
   every `goto ..._error` path frees what was allocated (no leak / no double free).

Until step 1 lands, `shada_read_next_item` stays `unverified` and the file is **not** finished.
