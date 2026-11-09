# shada.c: additional-data item count (`nitems`) wraps at 2^32

Status: **finding, fix not yet verified.** Pinned upstream
`7b87ce822e6fd45a4d9993599c2854afdb0dc4dd`. Found 2026-11-09 (lead from the msgpack-unpacker
thread). Sibling of the `nbytes` wrap in `push_additional_data` reported in verified_neovim#9;
this is the item-count half, which that fix does not cover.

## Where

`AdditionalData` (src/nvim/types_defs.h:69-74) counts its items in a **32-bit** field:

```c
typedef struct {
  uint32_t nitems;
  uint32_t nbytes;
  char data[];
} AdditionalData;
```

`push_additional_data` (src/nvim/msgpack_rpc/unpacker.c:604) does `a->nitems++` once per stored
item. In the ShaDa reader it is called once per trailing array element by
`shada_read_next_item` (src/nvim/shada.c, the loop
`for (uint32_t i = 0; i < read_additional_array_elements; i++) { ... push_additional_data(&ad, ...); }`)
and once per unknown dict key by `unpack_keydict`. Nothing clamps the running count.

## The wrap

The number of trailing items is bounded only by the size of the item, which
`shada_read_next_item` holds fully in memory (`buf = xmalloc(length)`), and `length` is accepted
up to `PTRDIFF_MAX`. A single entry (e.g. a Variable or SubString) whose trailing array has more
than 2^32 one-byte msgpack items (each nil/fixint is 1 byte, so an entry of a few GiB) makes
`nitems` wrap past 2^32 back to a small value. On the read paths that pass `max_kbyte == 0`
(`shada_read` → `shada_read_next_item(..., 0)`), no size limit stops such an entry.

`nitems` is read back by `additional_data_len` (shada.c:1330, `return src ? src->nitems : 0`) and
used on the **write** side to size the msgpack array header:

```c
uint32_t arr_size = 2 + (uint32_t)is_hist_search + additional_data_len(entry.additional_data);
mpack_array(&sbuf.ptr, arr_size);          // claims arr_size elements
...
dump_additional_data(entry.additional_data, &sbuf);   // writes all nbytes raw item bytes
```

After the wrap, `arr_size` is far smaller than the number of items `dump_additional_data`
actually emits (it copies `nbytes` raw bytes). The written ShaDa file then carries an array
header that under-counts its elements: the surplus item bytes trail the array, so a subsequent
read of that file misparses the entry or rejects it with "additional bytes". The result is a
corrupted / desynchronised ShaDa file on write-back, i.e. a data-integrity and round-trip bug.

## Severity

Not a memory-safety bug: `dump_additional_data` writes exactly `nbytes` bytes, all within the
allocated builder buffer, so there is no out-of-bounds access. It requires a multi-GiB entry held
in memory, so it is a large-input integrity/DoS wrap, not a small-input exploit. Severity: low,
but it breaks the reader↔writer invariant this file is supposed to maintain, so it is in scope.

## Proposed fix (to be verified, not yet done)

Make the count saturate-or-fail rather than wrap: have `push_additional_data` detect
`nitems == UINT32_MAX` (and, together with the #9 change, `nbytes + size` overflow) and signal
failure, and have `shada_read_next_item` treat that as a malformed entry
(`goto shada_read_next_item_error`). That bounds both counters and keeps the write-side
`arr_size` consistent with the data actually dumped. The fix needs its own proof (a bounded CBMC
harness over `push_additional_data` plus the read loop's termination/count) before it can be
marked `fixed`; that is the next step. No fix branch pushed yet.
