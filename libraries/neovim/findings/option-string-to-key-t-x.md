# `:set cedit=<t_x` reads one byte past the option value

**Where:** `src/nvim/option.c` at upstream 7b87ce822e6f, `find_key_len` (called by
`string_to_key`, which handles `'cedit'`, `'wildchar'` and `'wildcharm'`).

**What:** `string_to_key(arg)` calls `find_key_len(arg + 1, strlen(arg), true)`, so `len`
counts the `<` and `arg + 1` has `len - 1` bytes before its NUL. For a `t_xx` name it checks

```c
if (len >= 4 && arg[0] == 't' && arg[1] == '_') {
  if (!has_lt || arg[4] == '>') {
```

With the value `<t_x` (len 4), `arg + 1` is `"t_x"` and `arg[4]` is one byte past its NUL.

**Reproduced (function level):** `libraries/neovim/option/repro/string-to-key-t-x-repro.c`
runs the verbatim upstream `find_key_len` and `string_to_key` on a 5-byte heap copy of
`"<t_x"`: ASan reports a heap-buffer-overflow READ of size 1 in `find_key_len`. With the
fix it returns 0 (so `:set` reports E474), as it already did whenever that stray byte was
not `>`. Not yet run in a built `nvim` (`:set cedit=<t_x` or `:set wildchar=<t_x`).

**Impact:** a one-byte out-of-bounds read; the value read only decides whether the key is
accepted. Low severity.

**Fix:** `blooddimmedtide/verified_neovim` branch `claude/project-thread-33fn39`, commit
61856f2: `if (!has_lt || (len > 4 && arg[4] == '>'))`. The fixed `find_key_len` is proved
with WP (30/30); the same run on the upstream text fails at the `arg[4]` read.
