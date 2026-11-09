# xdl_blankline: a one-character last line counts as blank

File: `src/xdiff/xutils.c`, `xdl_blankline`, Neovim commit 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
(vendored from git's xdiff; git master has the same code).

```c
	if (!(flags & XDF_WHITESPACE_FLAGS))
		return (size <= 1);
```

Without a whitespace flag, every line of at most one byte is "blank". That assumes each line
ends with `\n`, so that size 1 means `"\n"`. The last line of a file need not end with a newline:
`"x"` without a newline has size 1 and is treated as blank.

## Effect (seen in Neovim 0.9.5 and git 2.43)

```
$ nvim --headless --clean -c 'lua io.stdout:write(vim.inspect(vim.diff("x", "y", {ignore_blank_lines = true})))' -c q
""
$ nvim --headless --clean -c 'lua io.stdout:write(vim.inspect(vim.diff("x", "y")))' -c q
"@@ -1 +1 @@\n-x\n\\ No newline at end of file\n+y\n\\ No newline at end of file\n"
```

With `ignore_blank_lines`, the change from `x` to `y` disappears. `git diff --no-index
--ignore-blank-lines` on two files holding `x` and `y` (no newline) also prints nothing (exit 1).
Neovim's own `:diffthis` with `diffopt+=iblank` is not affected, because it writes every buffer
line with a newline.

## Fix

Only `"\n"` and the empty line are blank: `return size == 0 || (size == 1 && line[0] == '\n');`
(fork branch `fix-xdiff-blankline-incomplete`). Proved with Frama-C WP in `../xdiff_xutils/`.
