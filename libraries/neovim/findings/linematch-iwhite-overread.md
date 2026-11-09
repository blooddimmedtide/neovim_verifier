# linematch.c: matching_chars_iwhite reads one byte past the buffer

Pinned upstream 7b87ce8, `src/nvim/linematch.c`, `matching_chars_iwhite`.

The copy loop runs `for (size_t i = 0; i <= slen; i++)` with
`slen = MIN(799, line_len(s))`. When the line has no `'\n'` and is shorter than 800 bytes,
`line_len(s) == s->size`, so the loop reads `s->ptr[s->size]`, one byte past the mmfile.

Evidence: CBMC (`linematch/cbmc`, harness `h_matching_chars_iwhite`, exact-size buffers)
reports `pointer outside object bounds in s->ptr[i]` on upstream. Not yet reproduced with ASan
in a real Neovim build. Reachable with `diffopt+=linematch:N,iwhite` when a compared line is
the last one of its block and carries no newline; Neovim's diff writer normally ends each line
with `'\n'`, so in practice the extra byte is usually inside the larger file buffer. Impact:
low (one-byte read, value only affects the alignment score).

Fix: verified_neovim branch `claude/project-thread-aaznxs` (e5db114):
`i <= slen && i < (size_t)s->size`. Every in-bounds read is unchanged, so results are the same.
The fixed function is proved by CBMC for buffers up to 2 bytes (bounded), both char signednesses.
Upstream issue: not drafted yet, not filed.
