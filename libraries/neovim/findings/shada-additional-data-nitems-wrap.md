# shada.c: additional-data array size (`2 + nitems`) wraps on write-back

Status: **finding, fix proved (counting invariant); integration into shada.c read path on the
fork.** Pinned upstream `7b87ce822e6fd45a4d9993599c2854afdb0dc4dd`. Found 2026-11-09 (lead from
the msgpack-unpacker thread, then narrowed on inspection). Complement of the `nbytes` wrap fixed
in verified_neovim#9.

## Corrected characterisation

The original lead was "the item count wraps past 2^32". On inspection that is **not** what
happens, and this note records the accurate defect:

- `AdditionalData.nitems` is `uint32_t` (src/nvim/types_defs.h:69-74), incremented once per item
  by `push_additional_data` (unpacker.c:604).
- The per-entry builder `ad` is reset at the top of `shada_read_next_item` (shada.c:3130), and the
  items it receives come from **one** msgpack container — the trailing array (`unpack_array`, its
  length `read_additional_array_elements`) for History/Variable/SubString, or the unknown keys of
  one map (`unpack_keydict`) for SearchPattern/Mark/Register. `mpack_token_t.length` is
  `mpack_uint32_t` (src/mpack/mpack_core.h:64), so a container header caps the count at
  `2^32 - 1`. Hence `nitems <= 2^32 - 1`: the **field itself does not wrap**.

The real defect is on the **write** side. `shada_pack_entry` rebuilds the entry's msgpack array
header from the count:

```c
uint32_t arr_size = (2 + (uint32_t)is_hist_search + additional_data_len(entry.additional_data));
// also: 2 + is_blob + len (Variable),  1 + len (SubString)
mpack_array(&sbuf.ptr, arr_size);
...
dump_additional_data(entry.additional_data, &sbuf);   // emits all nitems items
```

`additional_data_len` returns `nitems` (shada.c:1330). For an entry whose additional-item count is
within 3 of `UINT32_MAX`, `2 + nitems` / `3 + nitems` **overflows the `uint32_t` `arr_size`** and
`mpack_array` writes a header claiming far fewer elements than `dump_additional_data` then emits.
The written ShaDa file is desynchronised and misparses on the next read. (At that count the array
is also not representable in msgpack at all — array32 maxes at `2^32 - 1` elements — so the only
correct behaviour is to reject the entry, not to write it.)

## Reachability and severity

Reaching it needs a single entry carrying ~`2^32` additional items — each item is >=1 byte of the
in-memory item buffer, so a >~4 GiB entry, and `length` is accepted up to `PTRDIFF_MAX` with
`max_kbyte == 0` on the `shada_read` path. Large-input only. No out-of-bounds access (every write
stays in the allocated builder/packer buffers), so this is a data-integrity / round-trip-corruption
defect, not a memory-safety bug. Severity: low, but it breaks the reader<->writer invariant this
file must maintain, so it is in scope.

## Fix (proved invariant; fork integration)

Reject the un-writable entry on read, so it is never stored or written back: in
`shada_read_next_item`, after the additional-data array is built, if its item count exceeds
`UINT32_MAX - 3` (the largest count for which every write-side `k + nitems`, `k <= 3`, stays within
`uint32_t` and within msgpack's array32 limit), go to the entry-error path. CBMC proof of the
guard's arithmetic is in `shada/cbmc/harness.c` (`h_arrsize_guard`): for every `nitems` the guard
admits, each of `1 + nitems`, `2 + nitems`, `3 + nitems` equals its `uint32_t` truncation (no wrap)
and is `<= 0xFFFFFFFF`; for every `nitems` it rejects, some `k + nitems` wraps. Non-vacuous
(`mutants.toml` `arrsize-guard-off-by-one`).

The guard is on the shada.c read side only, so it does not touch `push_additional_data` and does
not conflict with verified_neovim#9 (which widened `nbytes` to `size_t`); the two compose. Full
verification of `shada_read_next_item` itself (needed to mark this `fixed` rather than
`fixed-candidate`) still depends on modelling the MessagePack unpacker and remains future work.
