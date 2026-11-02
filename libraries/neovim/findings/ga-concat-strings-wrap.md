# ga_concat_strings: the result length can wrap around (heap overflow)

File: `src/nvim/garray.c`, `ga_concat_strings`, Neovim commit 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd.

```c
size_t len = 0;
for (size_t i = 0; i < nelem; i++) {
  len += strlen(strings[i]);
}
len += (nelem - 1) * strlen(sep);
char *const ret = xmallocz(len);
```

The sum is not checked. The array may hold the same pointer many times, and the separator is
repeated `nelem - 1` times, so the true length can exceed `SIZE_MAX` even though every string
fits in memory. The size then wraps, `xmallocz()` returns a short buffer and the `xstpcpy` loop
writes past it.

## Reachability

Needs a true length of 2^64 bytes or more. `ga_len` is an `int`, so at most 2^31 - 1 items: for
example 2^31 - 1 copies of one pointer to a string of 2^33 + 5 bytes, or a separator of 2^33 + 5
bytes with 2^31 - 1 items. That takes 16 GiB for the pointer array plus the 8 GiB string. Every
current caller passes separate heap strings and a separator of at most one byte, so it cannot wrap
today (checked by the independent review). Found by the proof (the upstream contract needs
`total <= SIZE_MAX`), not observed.

## Fix (verified_neovim, branch `claude/project-thread-aslfna`, commit dec9b23)

Check each addition and the separator product; when the length does not fit, exit with the
message `xmallocz()` already uses for sizes that do not fit. Proved for every input with Frama-C
WP (`garray/wp`, mode `fixed`).

## Severity

Low and latent: no current caller can reach it; it would be an out-of-bounds heap write if a
future caller did.
