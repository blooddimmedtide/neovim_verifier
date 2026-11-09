# `:set opt+=x` corrupts memory once a comma-list option value reaches 2 GiB

**Where:** `src/nvim/option.c` at upstream 7b87ce822e6f: `stropt_concat_with_comma`,
plus the same pattern in `stropt_get_newval` and `stropt_expand_envvar`.

**What:** `stropt_concat_with_comma` stores `strlen(origval)` in an `int`:

```c
int len = 0;
...
len = (int)strlen(origval);
...
memmove(newval + len + comma, newval, strlen(newval) + 1);
memmove(newval, origval, (size_t)len);
```

For an option value of 2^31 bytes or more, `len` is negative: the first `memmove` writes
before `newval`, and `(size_t)len` in the second is about 2^64. Related casts in the
same `:set` path:

- `stropt_get_newval`: `s = origval + (int)strlen(origval);`, so for the same values `s`
  points before `origval` (then `stropt_remove_val` reads `*s`).
- `stropt_expand_envvar`: `uint32_t newlen = (unsigned)strlen(s) + 1; newlen += (unsigned)strlen(origval) + 1;`
  wraps once the two values add up to 4 GiB, so `xmalloc` returns a buffer that is too
  small for the `STRCPY` and the concatenation that follow.
- `stropt_remove_val(..., int len)` gets `(int)strlen(newval)` (a 2 GiB `-=` argument). Not fixed yet.

**Reproduced (function level):** `libraries/neovim/option/repro/concat-over-2gib-repro.c`
runs the verbatim upstream `stropt_concat_with_comma` with a 2^31 + 16 byte `origval` and
`newval = "b"`, as `:set wildignore+=b` does. With glibc fortify it aborts with
`*** buffer overflow detected ***`; built with the fixed text it returns the expected
2^31 + 18 byte result. Not yet reproduced end to end in a built `nvim` (needs several GiB of
RAM and a full build; this session ran out of time).

**Fix:** `blooddimmedtide/verified_neovim` branch `claude/project-thread-33fn39`, commit
36f4ea6: `size_t` lengths in all three places. The fixed `stropt_concat_with_comma` is not
yet proved with WP.

**How found:** reading the callers of the comma-list helpers while writing their contracts
(`libraries/neovim/option/wp`); `(int)` on a `size_t` length is the pattern AGENTS.md lists as
the most common bug so far. A WP run of the upstream function with `-warn-signed-downcast`
has not been done yet.
