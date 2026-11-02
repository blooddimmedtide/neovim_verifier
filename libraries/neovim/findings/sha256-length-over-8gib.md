# sha256_update counts input lengths of 8 GiB or more wrongly (wrong SHA-256)

File: `src/nvim/sha256.c`, `sha256_update`, Neovim commit 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd.

```c
ctx->total[0] += (uint32_t)length;
ctx->total[0] &= 0xFFFFFFFF;
if (ctx->total[0] < length) {
  ctx->total[1]++;
}
```

`total[1]:total[0]` is the 64-bit byte count that `sha256_finish` encodes into the padding.
`length` is a `size_t`. The update adds only its low 32 bits, and the carry test compares the
new 32-bit low word with the full 64-bit `length`, so it adds at most 1 to the high word. For
one call with `length >= 2^33` (or `>= 2^32` when the low words also carry) the count is wrong,
the length field in the padding is wrong, and the digest is not the SHA-256 of the input.

## Reproduce

```
gcc -O2 -I<stubs> src/nvim/sha256.c sha256-over-8gib-repro.c -o big   # stubs: see repro header
./big 8589934597    # 8 GiB + 5 bytes of 'a'
9697b2fb767265f089d05b09967800cfdc4a62e187cd28a06c34dc101a56b76c   (Neovim)
4c2f5c72671382e83a43a158197c767b71f1075ab554ad1598306824793c3847   (Python hashlib, correct)
```

At 4 GiB + 3 bytes the result happens to be right (the high word should be 1, and the faulty
carry test adds exactly 1).

## Reachability

- `sha256({string})` (Vimscript) and `vim.fn.sha256()` hash the whole string in one call.
  A string of 8 GiB or more gives a wrong hash.
- `vim.secure.read()` hashes whole files this way (trust database). Reading an 8 GiB file needs
  a PUC Lua build (LuaJIT strings stop below 2 GiB).
- Undo files and `:w` hash per line; a single line of 8 GiB would be needed.

## Fix

```c
uint32_t len_lo = (uint32_t)length;
ctx->total[0] += len_lo;
if (ctx->total[0] < len_lo) {
  ctx->total[1]++;
}
ctx->total[1] += (uint32_t)((uint64_t)length >> 32);
```

The 64-bit byte count is then exact for every message SHA-256 accepts (under 2^64 bits, i.e. 2^61 bytes).

## Severity

Low: a wrong digest for inputs of 8 GiB or more. It does not give a collision with a correctly
hashed message (the padding of the wrong digest is not a valid padding of any other message).
