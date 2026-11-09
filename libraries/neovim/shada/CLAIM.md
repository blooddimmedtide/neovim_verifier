---
entry: neovim/src/nvim/shada.c (ShaDa file reader: untrusted-input primitives)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
toolchain: CBMC (bit-precise bounded model checking)
strength: candidate   # becomes full-correctness after the owner signs off the spec
platform: x86_64, char signed (Neovim's build) and unsigned (both proved)
scope: partial   # only the functions in the table below; see "Not yet verified"
---

# Claim card: Neovim shada.c reading primitives

The ShaDa (`~/.local/state/nvim/shada/main.shada`) file is read on startup and can come from
an untrusted source (a shared home, a crafted file). This card covers the low-level functions
that pull bytes out of that file and the MessagePack integer decoder that sizes every entry.
They are the functions an attacker reaches first, before any entry payload is parsed.

## What is proved, for every input

The code under test is a verbatim extraction of these functions from `src/nvim/shada.c`
(`cbmc/build.py`, each function pinned by sha256). The file is modelled by `cbmc/model.h`:
a byte array `data[0..size)` with a read cursor, where `file_read` copies
`min(len, remaining)` bytes and sets EOF when it returned short, and where any one call may
instead fail with a negative errno after consuming an unknown number of bytes (as `os_read`
can). That is the exact contract `shada.c` relies on from `os/fileio.c` for a blocking read.

| Function | Property proved against an independent reference |
|---|---|
| `vim_be64toh(x)` | returns the 8 memory bytes of `x` read as a big-endian number (reference: `cbmc/spec.h` `spec_be`). This is the portable branch Neovim compiles when `be64toh` is absent |
| `fread_len(r, buf, len)` | returns Success iff exactly `len` bytes were available, and then `buf[0..len)` equals the next `len` file bytes; NotShaDa on short read (cursor at EOF); ReadError on a read failure. Writes nothing past `buf[len-1]` |
| `sd_reader_skip(r, off)` | returns Success iff `off` bytes were available and advances the cursor by exactly `off`; NotShaDa on short skip; ReadError on failure |
| `msgpack_read_uint64(r, allow_eof, res)` | decodes one MessagePack **unsigned** integer (positive fixint, uint8/16/32/64) and returns its exact value; Finished at EOF when `allow_eof`, else NotShaDa; NotShaDa on any non-unsigned lead byte (consuming exactly the one byte) or a cut-off payload; ReadError on failure; `*res` is left unchanged on every non-Success path. Reference: `cbmc/spec.h` written from the MessagePack spec, not from the switch in the code |

Each is proved under CBMC with `--bounds-check --pointer-check --conversion-check
--signed-overflow-check --unsigned-overflow-check --undefined-shift-check` and
`--unwinding-assertions` (every loop fully unwound), for signed and unsigned `char`. The
file objects are exact-size, so any read past the modelled file length fails the pointer
check. `*res`/`bytes_read` tracking is checked exactly, so the integer decoder cannot report
a wrong length to its caller — which is what `shada_read_next_item` trusts to size each item.

## Not yet verified (completion rule)

`shada.c` has ~60 functions. Only the five primitives above are proved. Still open, and so
this file is **not** finished: `shada_read_next_item` (the large entry parser) and its helpers
`shada_check_status`, `shada_read`, `shada_read_file`, the `hmll_*`/`hms_*`/`marklist_*`
history and mark structures, and the writer side. `shada_read_next_item` depends on the whole
MessagePack unpacker (`unpack_keydict`, `unpack_array`, `unpack_string`, `unpack_typval`) and
the arena/dict machinery; verifying it needs those modelled first. Progress is tracked in
`status.tsv`; see the PR for the live list.
