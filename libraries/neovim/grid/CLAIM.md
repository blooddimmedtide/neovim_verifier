# grid.c schar helpers: claim (candidate)

Upstream `src/nvim/grid.c` at 7b87ce8. **Not finished: 9 of 48 functions proved.** Tool: CBMC 6.4.1,
x86_64 (little-endian), signed and unsigned `char`, `--bounds-check --pointer-check
--signed-overflow-check --undefined-shift-check --unwinding-assertions`, no malloc failure.
Run: `bash grid/cbmc/run_cbmc.sh <neovim checkout>` (18/18 proved).

## What is proved (every 32-bit input)

The reference (`cbmc/spec.h`) is written from the meaning of `schar_T` given in grid.c's
comment and types_defs.h: 4 bytes in memory; byte 0 == 0xFF marks a glyph-cache cell whose other
3 bytes are a little-endian byte offset into `glyph_cache.keys`; otherwise the bytes are the
glyph's UTF-8 text, NUL padded.

| Function | Property |
|---|---|
| schar_high | true iff byte 0 is 0xFF |
| schar_get_ascii | the byte if the cell is exactly one byte < 0x80, else NUL |
| schar_len | length of the cell's text (inline or cached) |
| schar_get_adv | copies exactly that text to `*buf_out`, advances it by the length, no NUL, no out-of-bounds read or write |
| schar_get | same, plus a NUL after it, inside a `MAX_SCHAR_SIZE` buffer |
| schar_get_first_byte (static) | first byte of the text |
| schar_in_arabic_block (static) | true iff first byte is 0xD8 or 0xD9 (UTF-8 lead bytes of U+0600..U+07FF) |
| schar_from_char | bytes = UTF-8 of `c`, zero padded; `c >= 0x200000` gives U+FFFD (the code's own decision) |
| grid_adjust | returns `grid->target`, adds the offsets (see precondition 3) |

`schar_from_char` runs the real `utf_char2bytes` (mbyte.c, sha pinned), not a stub.

## What it relies on

1. Glyph cache model (`cbmc/prelude.h`): `keys` is an exact-size object of `n_keys` bytes
   (n_keys 1..40); for a high cell, `idx < n_keys` (the code's own `assert`) and a NUL within
   `MAX_SCHAR_SIZE` bytes of `idx` (cache invariant: glyphs are shorter than MAX_SCHAR_SIZE,
   mh_put_glyph NUL-terminates each). Not proved here: that every live cell's offset is a valid entry
   (true only until `schar_cache_clear`, as its comment says).
2. Non-high cells are NUL padded (no NUL followed by a non-NUL byte), the representation every writer
   produces (schar_from_buf/schar_from_char). `schar_high` / `schar_get_ascii` / `schar_from_char` need no such
   assumption.
3. **grid_adjust: undocumented precondition** that `*row_off + row_offset` and `*col_off + col_offset`
   fit in `int` (screen coordinates). Without it CBMC reports signed overflow. Owner to decide if this is
   acceptable; until then treat grid_adjust as proved only under it.
4. `c >= 0` for schar_from_char (documented: "a unicode character").
5. POSIX `strnlen` (modelled in prelude.h; CBMC has no body).
6. The `schar_idx` little-endian macro is copied verbatim (build.py fails if it changed).

## Evidence

| Check | Result |
|---|---|
| `run_cbmc.sh` upstream 7b87ce8 | 9 harnesses x 2 char signednesses: 18/18 proved |
| `mutants.sh` planted bugs | 10/10 caught (checked one by hand: fails on the assertion, not the pin) |
| Differential test, independent review, big-endian | not done |

No bug found in these functions.
