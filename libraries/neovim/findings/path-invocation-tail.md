# path.c: invocation_path_tail reads past the end of the string

- **Upstream**: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd, `src/nvim/path.c`, `invocation_path_tail()`
- **Found by**: Frama-C WP, `-wp-rte` (loop invariant `p` stays inside the string is not preserved); confirmed with ASan.
- **Fix**: `blooddimmedtide/verified_neovim` branch `claude/project-thread-t2grsh` (commit ae63bc4), proved with WP (40/40 goals, both char signednesses).

## What goes wrong

Inside double quotes a backslash skips the next character:

```c
} else if (*p == '\\' && inquote) {
  p++;
} ...
p += l;   // l = utfc_ptr2len() of the backslash, computed before p++
```

When the backslash is the last byte of the string, `p++` lands on the NUL and `p += l`
(l = 1) steps past it. The loop then keeps reading bytes after the string until it meets a
NUL or a space. The same happens when the backslash is followed by a composing character
(`utfc_ptr2len` of the backslash then covers the composing character too, so `p++` plus `l`
skips one byte more than the string has left).

Reproducer: `path-invocation-tail/repro.c` (the function text verbatim, a 5-byte heap copy of
`"sh\` ). `gcc -g -fsanitize=address repro.c && ./a.out` reports a heap-buffer-overflow READ
of size 1, 0 bytes after the 5-byte region.

## Reachability

Every caller passes the `'shell'` option value (`p_sh`): `set_init_3()` in option.c (at start,
after the user's config), `make_filter_cmd()` in ex_cmds.c, and `os_expand_wildcards()` in
os/shell.c. A config with `set shell="sh\` (or a `$SHELL` with that shape) triggers the
over-read. In `set_init_3()` the bad `len` is then used for `xmemcpyz(name, p, len)` into a
`MAXPATHL` stack buffer.

Lead for the option.c owner (not proved or reproduced here): `set_init_3()` copies `len`
bytes into `char name[MAXPATHL]` with no bound, so a `'shell'` value whose executable name is
longer than MAXPATHL - 1 bytes may overflow `name` even without this bug.

## Fix

```c
} else if (*p == '\\' && inquote) {
  // Skip the backslash and the whole character after it, but never the NUL.
  p++;
  l = utfc_ptr2len(p);
}
```

`utfc_ptr2len` returns 0 at the NUL, so the loop stops there. This also makes "a backslash
skips the following character" true for multibyte characters.
