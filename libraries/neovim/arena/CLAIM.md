# Claim: arena allocator in src/nvim/memory.c (partial, stopped at the 2026-11-09 09:00 UTC deadline)

Pinned upstream: neovim/neovim `7b87ce822e6fd45a4d9993599c2854afdb0dc4dd`, `src/nvim/memory.c`
lines 679-829 (from `#define REUSE_MAX 4` to the end of `arena_strdup`), sha256
`3fd72a7c8a75f2a6ecfb1b2e2ccaa2c7e4ff4407d0dc32f53c1a3cb64e47ef3c` (checked by `cbmc/build.py`).

Tool: CBMC 6.4.1, `--no-malloc-may-fail --unwinding-assertions --memory-leak-check`, pointer,
bounds and overflow checks, signed and `--unsigned-char` runs. Spec is in the header of
`cbmc/harness.c` (S1-S5), written from the comments in memory.c / memory_defs.h.

| Function | Status | Evidence |
|---|---|---|
| arena_align_offset | proved (S1) for every `off <= UINT64_MAX-7` | `H_ALIGN`, both signednesses |
| arena_alloc | proved (S2) for 3 consecutive calls, any size `<= SIZE_MAX-4096`, any align, both paths (normal block and large block) | `H_ALLOC`, both signednesses, 279 checks |
| arena_alloc | **finding** for sizes above `SIZE_MAX-4096` (`findings/arena-alloc-size-wrap.md`). Fix on blooddimmedtide/verified_neovim branch `fix-arena-alloc-size-wrap` proved for **every** size (S2, both signednesses) | upstream `H_ALLOC -DSIZE_LIMIT=SIZE_MAX` fails; fork `H_ALLOC` passes |
| arena_allocz | upstream proved (S3) for size <= SIZE_MAX-4096; writes out of bounds at SIZE_MAX (same finding); fix proved for every size, both signednesses | `H_ALLOCZ` |
| arena_alloc_block, alloc_block (fresh path) | exercised inside `H_ALLOC` (first call allocates a block); not separately specified | partial |
| arena_finish, arena_mem_free, free_block, alloc_block (reuse path), arena_free_reuse_blks | **unverified**: `H_LIFE` written but ran out of memory (15 GB) at 2 rounds x 2 allocs | open |
| arena_memdupz, arena_strdup | **unverified**: `H_DUP` written but ran out of memory | open |

Assumptions: xmalloc never returns NULL (it exits on failure; sizes over 2^40 modeled as exit).
The harness precondition `size <= SIZE_MAX-4096` is NOT documented upstream; it is exactly the
finding, so the arena_alloc claim is "correct below that size, wrong above it".

Next steps: make H_LIFE / H_DUP fit in memory (use a smaller ARENA_BLOCK_SIZE stand-in is NOT
allowed since it changes the code; instead drop `--memory-leak-check` for the dup harness and
track frees with a ghost counter, or prove the lifecycle with Frama-C WP using ghost "avoid"
style from typval/wp_blob); independent review + mutants; difftest.
