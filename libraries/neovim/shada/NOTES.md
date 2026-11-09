# shada.c reader — analysis notes

Pinned commit `7b87ce822e6fd45a4d9993599c2854afdb0dc4dd`.

## Proved (shada/cbmc)
`vim_be64toh`, `fread_len`, `sd_reader_skip`, `msgpack_read_uint64`, `shada_check_status`
— full-correctness, all inputs, signed and unsigned char. See CLAIM.md.

## Integer/allocation sizing reviewed, no bug found
While planning the proof of `shada_read_next_item`, the item-sizing arithmetic was
checked by hand for overflow:

- `length_u64 > PTRDIFF_MAX` is rejected before `xmalloc(length)`, so the item buffer
  size is bounded and the allocation cannot wrap.
- History entry `strsize = item.size + 1 + 1` then `xmalloc(strsize)` with writes at
  `strsize-2`/`strsize-1`: `item.size` comes from `unpack_string` and is bounded by the
  already-read item buffer (`<= length <= PTRDIFF_MAX`), so `+2` cannot wrap `size_t`
  and the two trailing writes are in bounds.
- Register `xmalloc(it.rc.size * sizeof(String))`: `it.rc.size` is the count of strings
  actually pushed, each consuming >=1 byte of the in-memory item buffer, so it is bounded
  by `length`. The product can only overflow `size_t` for an item buffer of ~2^60 bytes,
  which `length_u64 > PTRDIFF_MAX` already forbids.

The one real wrap found is the additional-data **item count**: `AdditionalData.nitems`
(uint32) is incremented once per trailing additional-data item with no clamp, so an entry
larger than ~4 GiB wraps it, and the write side rebuilds the msgpack array header from the
wrapped count while `dump_additional_data` emits all the bytes -> a corrupted/desynchronised
ShaDa file on write-back. It is a data-integrity/DoS wrap, not a memory-safety bug (writes stay
in bounds). Documented, fix not yet verified, in
findings/shada-additional-data-nitems-wrap.md. It is the item-count sibling of the `nbytes`
wrap reported for push_additional_data in verified_neovim#9.

## Not verified (completion rule — shada.c is NOT finished)
`shada_read_next_item` and its callees `unpack_keydict`/`unpack_array`/`unpack_string`/
`unpack_typval` (in `src/nvim/msgpack_rpc/unpacker.c`), `shada_read`, `shada_read_file`,
`shada_read_marks`, `shada_read_everything`, the `hmll_*`/`hms_*`/`marklist_*` history and
mark data structures, and the entire writer side. Verifying `shada_read_next_item` needs the
MessagePack unpacker and the arena/dict machinery modelled first; that is the next step.
