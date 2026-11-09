# search.c: setcharsearch() with many composing characters overflows lastc_bytes

**File:** `src/nvim/search.c`, `set_last_csearch` (commit 7b87ce8).
**Found by:** reading the callers of the csearch state while fuzzing search.c; confirmed with
the ASan build (`../regexp_search/fuzz/`).
**Fix:** `blooddimmedtide/verified_neovim`, branch `claude/project-thread-legcap`, commit
`01c749d`. Proved for every input with CBMC (`../search/cbmc/`, see `../search/CLAIM.md`).

## What goes wrong

`set_last_csearch(c, s, len)` copies `len` bytes into `static char lastc_bytes[MAX_SCHAR_SIZE + 1]`
(33 bytes). Its only caller with untrusted input, `setcharsearch()` (eval/funcs.c), passes
`utfc_ptr2len(s)`: a base character plus all of its composing characters, which has no upper
limit. So

    :call setcharsearch({'char': 'a' .. repeat("́", 40)})

copies 81 bytes into the 33-byte buffer. ASan: `global-buffer-overflow ... WRITE of size 81`,
which overwrites `lastc_bytelen` and other search.c globals.

A second, smaller bug in the same code: the buffer is not cleared, so after a longer character
the bytes past the new character stay. `getcharsearch().char` reads `lastc_bytes` as a
NUL-terminated string:

| Steps | Upstream `getcharsearch().char` | Fixed |
|---|---|---|
| `setcharsearch({'char': "é̂"})` then `setcharsearch({'char': 'x'})` | `"x́̂"` (5 bytes) | `"x"` |
| same, then `fx` in Normal mode | `"x́̂"` | `"x"` |

The normal-mode path (`searchc`) cannot overflow: `nchar_composing` is limited to 31 bytes in
normal.c. It had the same stale-byte problem.

Reproducer: `search-csearch-overflow-repro.lua`.

## Fix

`set_last_csearch` keeps only the whole characters that fit in `MAX_SCHAR_SIZE` bytes (cut
back to the last byte that is not a UTF-8 trail byte, the same limit a screen cell has), and
both writers clear `lastc_bytes` before copying.

## Severity

Medium: a write past a static buffer, reachable from any Vimscript or Lua code
(`vim.fn.setcharsearch`), such as a plugin or a sourced script, but not from file contents
alone (modelines cannot call functions). Up to the whole string length is written, so it
can overwrite any globals placed after `lastc_bytes`; the usual effect is wrong `;`/`,`
behaviour or a crash.
