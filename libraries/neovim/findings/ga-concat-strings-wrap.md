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

Needs a true length of 2^64 bytes or more: for example `nelem = 2^31 - 1` copies of one pointer to
an 8 GiB string, or a separator of 2^33 bytes with 2^31 elements. That takes 16 GiB for the pointer
array plus the string; possible only on very large machines, and no current caller is known to
pass such an array. Found by the proof (the upstream contract needs `total <= SIZE_MAX`), not
observed.

## Fix (verified_neovim, branch `claude/project-thread-aslfna`, commit dec9b23)

Check each addition and the separator product; when the length does not fit, exit with the
message `xmallocz()` already uses for sizes that do not fit. Proved for every input with Frama-C
WP (`garray/wp`, mode `fixed`).

## Severity

Low in practice (needs more than 16 GiB of carefully built input), but it is an out-of-bounds
heap write when it happens.
