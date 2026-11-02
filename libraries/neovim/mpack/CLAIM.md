---
entry: neovim/src/mpack/mpack_core.c (libmpack tokenizer, vendored in Neovim)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch fix-mpack-chunk-over-4gib, commit 1778674; all fixes: branch verified)
toolchain: CBMC 6.4.1 (.deb, see tools/install.sh), gcc for the differential test
container: ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac (CI)
strength: candidate   # becomes full-correctness after the reviews and the owner's spec sign-off
tools: CBMC 6.4.1 (every loop fully unwound, proved by unwinding assertions)
platform: x86_64, char signed and unsigned (both proved)
---

# Claim card: Neovim src/mpack/mpack_core.c

The file is proved as it is: `harness.c` includes the upstream file unchanged (no extraction,
no tool patch). The reference (`cbmc/spec.h`) is written from the MessagePack specification.

## What is proved, for every input

| Function | Property |
|---|---|
| `mpack_rtoken(buf, len, tok)` | Reads the token the MessagePack spec defines for the bytes at `buf` and consumes exactly its header; `MPACK_ERROR` for 0xc1; `MPACK_EOF` when the header is incomplete, with `tok->length` = header size - 1. Reads nothing past `len` or past the header |
| `mpack_wtoken` (static) | For every token Neovim builds (see preconditions), writes the shortest encoding the spec allows, which decodes back to the same value; `MPACK_ERROR` for a float that is not 4 or 8 bytes |
| `mpack_read(tb, buf, len, tok)` | From any tokbuf state the invariant allows: an empty input changes nothing; while payload is due, returns one CHUNK of min(input, remaining payload) bytes pointing into the input; otherwise returns the spec token of (pending header bytes + input), consumes only the rest of its header and sets the payload count for str/bin/ext, or keeps an incomplete header in `pending` and consumes all input, or returns `MPACK_ERROR` without changing the state. The invariant holds again after every call. Fixed fork: any input length. Upstream: input under 4 GiB (see Finding) |
| `mpack_write(tb, buf, len, tok)` | From any tokbuf state the invariant allows: writes the next min(room, rest) bytes of the encoding of the pending token, or of `tok` (shortest encoding), or of a CHUNK's bytes, in order; returns `MPACK_OK` when the token is complete, else `MPACK_EOF` with the rest kept |
| `mpack_tokbuf_init` | sets the empty state, which satisfies both invariants |
| the 18 static helpers (`mpack_rpending`, `mpack_rvalue`, `mpack_rblob`, `mpack_wpending`, `mpack_wpint`, `mpack_wnint`, `mpack_wfloat`, `mpack_wstr`, `mpack_wbin`, `mpack_wext`, `mpack_warray`, `mpack_wmap`, `mpack_w1`, `mpack_w2`, `mpack_w4`, `mpack_value`, `mpack_blob`, `mpack_byte`) | proved through the functions above, for every input those functions can pass them (memory safety, no overflow, results as above). They are static, so no other caller exists |

**Streams.** Because each call is proved from any state the invariant allows, and returns to
such a state, induction over calls gives: reading a byte stream split into buffers at any
points yields the same tokens as reading it whole, and writing tokens into buffers of any
sizes produces the concatenated encodings.

## Finding

Upstream `mpack_read` casts the input length to 32 bits when passing payload. With a
multiple of 4 GiB of input left it returns empty chunks forever and `mpack_parse` hangs
(`vim.mpack.decode` on a string over 4 GiB in a PUC Lua build). Details and reproducer:
`../findings/mpack-chunk-over-4gib.md`. The fix is proved for every input length.

## What the proof relies on

1. **CBMC is sound** for this code (bit-precise C, x86_64 data model).
2. **Implementation-defined conversions:** `(char)` of a value above 127 keeps the low 8 bits.
3. **Preconditions** (harness `__CPROVER_assume`s):
   - `mpack_write`: `*buflen >= 1` (its own `assert`); tokens as `mpack_pack_*` builds them: a
     SINT holds a negative 64-bit value, an ext type is 0..127 (`mpack_wext` asserts it and
     lmpack's packer checks it), a 4-byte float has its bits in `lo`; a CHUNK points to
     `length` readable bytes.
   - Separate tokbufs for reading and writing (the writer leaves `ppos` set after a chunk,
     which the reader would subtract). Every caller in Neovim does this.
   - Reader state: nothing pending, or a partial header whose size matches its first byte;
     never both a pending header and pending payload. `mpack_tokbuf_init` and every call keep this.
4. **Long inputs:** reads never go past the 9-byte header (pointer checks on exact-size objects).
5. **Not sign-extended:** tokens returned by `mpack_read` keep the raw bits of the integer
   (libmpack's documented format); `mpack_unpack_sint` (conv.c, not covered here) sign-extends.

## Not covered

- `conv.c`, `object.c`, `rpc.c`, `lmpack.c` (the rest of src/mpack).
- Owner sign-off on the spec (Yerin). Independent review and planted bugs: pending.

## Evidence

| Check | Command | Result |
|---|---|---|
| CBMC, upstream | `bash cbmc/run_cbmc.sh <nvim>` | 5 / 5 harnesses, signed and unsigned char |
| CBMC, fixed fork | `bash cbmc/run_cbmc.sh <verified_neovim>` | 5 / 5 harnesses, signed and unsigned char |
| Differential test | `bash cbmc/run_difftest.sh <nvim>` | 92,445,377 checks, 0 mismatches (every input up to 3 bytes; random 9-byte inputs; 2,000,000 random token streams written and read back with random buffer splits) |
| Independent review | `cbmc/REVIEW.md` | pending |
| Planted bugs | `python3 -I cbmc/run_mutants.py <nvim>` | pending (reviewer's choice) |
| CI, pinned container, twice | `.github/workflows/verify.yml` | pending |
| Owner review | Yerin | pending |
