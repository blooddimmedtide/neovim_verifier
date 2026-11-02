# src/cjson/strbuf.c — work in progress (not a candidate yet)

Pinned: Neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. Fixed fork: blooddimmedtide/verified_neovim
branch `claude/project-thread-gritim` (PR #7 into `verified`).
Tools: CBMC 6.4.1 (`cbmc/run_cbmc.sh`, x86_64, signed and unsigned char), Frama-C 33 WP for the unbounded loop.

## Spec source
The comments in strbuf.h / strbuf.c: `size` is the bytes allocated to `buf`, `length` the string
length without the optional NUL, and there is always room for that NUL, so a strbuf in use has
`length < size` and `buf` holds `size` bytes. The reference decides nothing else.

## Status per function (upstream and fixed unless noted)

| Function | Status | Proved property |
|---|---|---|
| `die` | proved (CBMC) | never returns (abort) |
| `strbuf_init` | proved (CBMC) | `size = len ? len + 1 : 1023`, fresh block of exactly that size holding "", counters 0; dies only when `len + 1` overflows or malloc fails |
| `strbuf_new` | proved (CBMC) | as `strbuf_init` in a fresh struct, `dynamic = 1` |
| `debug_stats` | proved (CBMC) | changes nothing (debug output only) |
| `strbuf_free` | proved (CBMC) | frees `buf` (if not NULL) and, when dynamic, the struct; nothing else; a second call frees nothing |
| `strbuf_free_to_string` | proved (CBMC) | returns `buf`, NUL at `length`, `*len = length` when `len` is not NULL; frees the struct iff dynamic |
| `calculate_new_size` | proved (CBMC) | dies iff `len == 0` or `len + 1` overflows; shrink exactly; `len + 1` when that is `>= SIZE_MAX / 2`; else the least `size * 2^k >= len + 1` |
| `strbuf_resize` | proved (CBMC) | new size as above, block of exactly that size, first `min(old, new)` bytes kept, `length` kept, `reallocs + 1`; dies only on a bad `len` or realloc failure |
| `strbuf_append_string` | OPEN | upstream: int overflow at 2^31 bytes (findings/cjson-strbuf-append-over-2gib.md). CBMC proves both versions for strings up to 5 bytes; the unbounded WP proof of the fixed code is 48/49 goals (the loop's memory frame across a moved buffer is left) |

strbuf.h helpers (CBMC, `h_helpers`): reset, allocated, empty_length, empty_ptr, length, string,
ensure_null, ensure_empty_length, append_char, append_char_unsafe, append_mem, append_mem_unsafe,
extend_length are proved; `strbuf_set_length(s, int len)` is OPEN (an `int` length: negative values
turn into huge lengths; see the lua_cjson.c callers that pass an `int` position).

## What the proofs rely on
- CBMC 6.4.1 and its C front end are sound; the allocation model in `cbmc/model.h` (malloc/realloc
  may fail at any call and always above 2^50 bytes; realloc keeps min(old, new) bytes; abort does
  not return).
- `reallocs < INT_MAX / 2` in the harness: it counts resizes, each of which needs a larger buffer
  (a strbuf would need 2^30 resizes to reach it).
- `debug == 0` except in `h_debug_stats` (lua_cjson never sets it).
