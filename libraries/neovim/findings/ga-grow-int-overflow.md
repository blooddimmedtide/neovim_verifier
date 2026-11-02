# ga_grow overflows `int` once a growing array holds more than about 1.43e9 items

File: `src/nvim/garray.c`, `ga_grow`, Neovim commit 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd.

```c
n = MAX(n, gap->ga_growsize);
n = MAX(n, gap->ga_len / 2);
int new_maxlen = gap->ga_len + n;
```

`ga_grow` always grows by at least half the current length. When `ga_len >= 1,431,655,766`
(the smallest length with `ga_len + ga_len / 2 > INT_MAX`) and the array is full, `ga_len + ga_len / 2` does not fit in an `int`:
signed overflow, which is undefined behavior (Neovim is not built with `-fwrapv`). In practice the
sum wraps negative, `(size_t)new_maxlen` becomes about 1.8e19, `xrealloc` fails and Nvim exits
through `preserve_exit()` with "E41: Out of memory!", although the request (a few more bytes)
fits easily and `ga_concat_len` itself accepts arrays up to `INT_MAX` bytes.

## Reproduce

Standalone (upstream text of `ga_set_growsize`, `ga_init`, `ga_grow`, `ga_concat_len`):

```
gcc -O1 -g -fsanitize=undefined ga-grow-int-overflow-repro.c -o r && ./r
ga-grow-int-overflow-repro.c:50:7: runtime error: signed integer overflow: 1500000000 + 750000000 cannot be represented in type 'int'
E342: Out of memory (size 18446744071664584320), preserve_exit
```

Real Nvim (Ubuntu 24.04 `neovim` 0.9.5, same `ga_grow`), 15 GB machine with 10 GB free:

```
$ nvim --clean --headless -c "let s = join([repeat('a', 1500000000), 'x'], '') | echo strlen(s) | qa!"
E41: Out of memory!
Vim: Finished.
$ nvim --clean --headless -c "let s = join([repeat('a', 1400000000), 'x'], '') | echo strlen(s) | qa!"
1400000001
$ nvim --clean --headless -c "let s = repeat('a', 1500000000) | let t = string(s) | qa!"
E41: Out of memory!
```

## Reachability

Every growing array: `join()`, `string()`, `:echo`, `json_encode()` and `msgpackdump()` output,
`:redir` into a variable, and so on. Any string built in a garray that passes 1,431,655,766 bytes
and then grows once more ends Nvim. Both commands above exit; the independent review traced the
`join` case to the growing array `encode_tv2echo()` uses (its final `ga_append(NUL)`), so echoing or
stringifying any string of that size is enough.

## Fix (verified_neovim, branch `claude/project-thread-aslfna`, commit 850a906)

```c
if (n > INT_MAX - gap->ga_len) {
  preserve_exit(_("Nvim: Data too large to fit into virtual memory space\n"));
}
const int room = INT_MAX - gap->ga_len;
n = MAX(n, MIN(gap->ga_growsize, room));
n = MAX(n, MIN(gap->ga_len / 2, room));
```

The extra growth (growsize and the 1.5 factor) stops at `INT_MAX` items; a request that cannot fit
in an `int` at all (only possible from callers that do not check, such as `GA_APPEND` at exactly
`INT_MAX` items) exits with the message `xmallocz()` uses, instead of overflowing. Proved for every
input with Frama-C WP (`garray/wp`, mode `fixed`).

## Severity

Medium: Nvim exits (after preserving swap files) instead of building a string between 1.43e9 and
2^31 - 1 bytes. Strictly it is undefined behavior, so a compiler may do worse.
