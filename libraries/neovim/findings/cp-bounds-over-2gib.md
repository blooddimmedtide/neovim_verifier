# utf_cp_bounds_len: wrong result, undefined behavior and out-of-bounds read when p is 2 GiB or more past base

**File:** `src/nvim/mbyte.c`, `utf_cp_bounds_len` (commit 7b87ce8), and its callers in `src/nvim/lua/stdlib.c`.
**Found by:** the CBMC proof in `../mbyte/cbmc/harness_bounds.c` (it fails without the precondition `p - base <= INT_MAX`).
**Fix:** `blooddimmedtide/verified_neovim`, branch `fix-cp-bounds-over-2gib`, proved for every distance.

## What goes wrong

```c
int const max_first_off = -MIN((int)(p - b), MB_MAXCHAR - 1);
```

`(int)(p - b)` keeps only the low 32 bits of the distance from `base` to `p`. Three outcomes:

| Distance `p - base` | `(int)(p - b)` | Effect |
|---|---|---|
| below 2^31 | correct | correct |
| exactly 2^31 (mod 2^32) | `INT_MIN` | `-INT_MIN` overflows: undefined behavior |
| 2^31 + k, k < 2^31 | negative | `max_first_off` is positive and never reached: the backward scan over continuation bytes does not stop after 5 bytes. On a run of continuation bytes back to `base` it reads before the buffer (ASan: SEGV, `READ`) |
| 2^32 + k, small k | small positive | the scan gives up after k bytes: `(0, 1)` for a valid character whose lead byte is further back (wrong result) |

Reproducer: `cp-bounds-over-2gib-repro.c` (ASan + UBSan report the overflow and the out-of-bounds read at 2^31 + 1; plain `-O2` gives `(0, 1)` instead of `(2, 1)` at 2^32 + 2).

## Reachability

`vim.str_utf_start(s, i)` and `vim.str_utf_end(s, i)` (`lua/stdlib.c`) call
`utf_cp_bounds_len(s1, s1 + off, (int)(s1_len - off))`. With a Lua string longer than 2 GiB
and an index past 2^31 the bug is reached. The same calls also truncate `p_len`, which can
make it 0 or negative (`assert(p_len > 0)` fires in builds with asserts).

LuaJIT, Neovim's default, caps strings below 2 GiB, so official builds are not affected through
this path. Builds with PUC Lua (`-DPREFER_LUA=ON`) are. The other callers (`grid.c`, `buffer.c`)
pass short buffers.

## Fix

```c
int const max_first_off = -(int)MIN(p - b, MB_MAXCHAR - 1);                    // mbyte.c
utf_cp_bounds_len(s1, s1 + off, (int)MIN(s1_len - off, (size_t)INT_MAX))     // lua/stdlib.c, twice
```

The fixed `utf_cp_bounds_len` is proved correct for every distance up to `PTRDIFF_MAX`
(`run_cbmc.sh <fixed checkout>`). The `stdlib.c` change is not machine-proved yet (it needs the
Lua API stubs); it only clamps the length to `INT_MAX`, which the proved function accepts.

## Severity

Low: it needs a string over 2 GiB in a PUC Lua build. Out-of-bounds read only, no write.

## Related latent issue (not a bug today)

`fileio.c:1228` calls `utf_byte2len(*tail)` with a `char`; with signed `char`, a byte ≥ 0x80
would index `utf8len_tab` with a negative value. The reviewer traced that this path needs a
conversion from UTF-8, which Neovim never sets up, so it is unreachable. A `(uint8_t)` cast
would remove the trap.
