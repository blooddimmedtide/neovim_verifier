# arena_alloc: size near SIZE_MAX wraps the bounds check (src/nvim/memory.c)

Pinned commit 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd, memory.c `arena_alloc` / `arena_allocz`.

- `if (alloc_pos + size > arena->size)` wraps when `size > SIZE_MAX - alloc_pos`; the check then
  passes and the function returns a pointer into the 4096-byte block for a request of ~2^64 bytes.
- In the large-block path, `xmalloc(size + aligned_hdr_size)` wraps when `size > SIZE_MAX - 8`,
  allocates a few bytes, and writes the header past the end (`fix_blk->prev`), heap overflow.
- `arena_allocz(a, SIZE_MAX)` calls `arena_alloc(a, 0, false)` (size+1 wraps) and then writes
  `mem[SIZE_MAX] = NUL`, far out of bounds.

Found by CBMC (`arena/cbmc/harness.c`, `H_ALLOC -DSIZE_LIMIT=SIZE_MAX`): overflow checks on
memory.c lines alloc_pos+size, size+aligned_hdr_size, and the pointer check on fix_blk->prev fail.

Reachability: not shown. Every caller seen so far passes sizes bounded far below this (msgpack
lengths are 32-bit). Severity: hardening, unless a caller computes a size that can wrap.
Fix (blooddimmedtide/verified_neovim branch `fix-arena-alloc-size-wrap`, proved with CBMC for every size, `H_ALLOC` and `H_ALLOCZ`): test `size > arena->size - alloc_pos`
instead of `alloc_pos + size > arena->size`, exit with out-of-memory (preserve_exit, like xmalloc)
when `size + header` would wrap in the large-block path, or when `size == SIZE_MAX` in arena_allocz.

Upstream issue: draft only; the owner decides whether to file.
