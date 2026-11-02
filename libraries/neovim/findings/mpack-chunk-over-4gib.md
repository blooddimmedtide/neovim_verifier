# mpack_read: empty chunks, no progress, when a multiple of 4 GiB of input remains

**File:** `src/mpack/mpack_core.c`, `mpack_read` (commit 7b87ce8).
**Found by:** the CBMC proof `../mpack/cbmc/harness.c` (`h_read`), which fails without the
precondition "input under 4 GiB".
**Fix:** `blooddimmedtide/verified_neovim`, branch `fix-mpack-chunk-over-4gib` (also on `verified`),
proved for every input length.

## What goes wrong

The payload of a str/bin/ext value is passed to the caller as CHUNK tokens:

```c
tok->length = MIN((mpack_uint32_t)*buflen, tokbuf->passthrough);
```

The cast keeps the low 32 bits of the input length. When the input left is a multiple of
2^32 bytes, the chunk is 0 bytes long and nothing is consumed, while `mpack_read` still
returns `MPACK_OK`. `mpack_parse` (`object.c`) loops `while (*buflen && status)`, so it
spins forever. (Other lengths of 4 GiB or more give chunks shorter than needed, which is
harmless.)

Reproducer: `mpack-chunk-over-4gib-repro.c` (a `bin 32` header followed by 4 GiB of payload;
the payload is never touched, so it needs no RAM). Output: `chunk length 0, 4294967296
bytes left`, again and again.

## Reachability

`vim.mpack.decode(s)` and `vim.mpack.Unpacker` (`lmpack.c`) hand the whole Lua string to
`mpack_parse`. A string of 4 GiB + header with a str/bin/ext inside hangs Neovim. LuaJIT,
Neovim's default, limits strings below 2 GiB, so that route needs a PUC Lua build. The RPC
unpacker reads from small channel buffers and is not affected.

ShaDa reaches it in a default (LuaJIT) build too (found by the second reviewer by reading
the code; not run, since it needs a 4 GiB file): when the first item of a ShaDa file has an
unknown type, `shada.c` (around lines 3170-3210) reads the item whole, regardless of the
size limit, and hands it to `unpack_skip` -> `mpack_parse`. A crafted ShaDa file with such
an item over 4 GiB would hang Neovim at startup.

## Fix

```c
tok->length = (mpack_uint32_t)MIN(*buflen, (size_t)tokbuf->passthrough);
```

The minimum is at most `passthrough`, so it fits in 32 bits.

## Severity

Low: a hang (denial of service) that needs over 4 GiB of msgpack input: a Lua string in a PUC Lua build, or a crafted ShaDa file in any build.

## Related note (not a bug today)

`mpack_write` encodes a SINT token as a 64-bit two's complement value. Tokens built by
`mpack_pack_sint` are; tokens returned by `mpack_read` are not sign-extended (an int 8 of -1
reads as lo = 0xff), so writing a read token back would change its value (to 255). No caller
in Neovim does that: writers build tokens with `mpack_pack_*`. The same goes for a tokbuf
used for both reading and writing (the writer leaves `ppos` set after a chunk, which the
reader would subtract); every caller uses separate tokbufs.
