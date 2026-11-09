# Huge line numbers wrap to small ones in tv_get_lnum() (candidate finding, not yet reported)

- File: `src/nvim/eval/typval.c`, `tv_get_lnum` and `tv_get_lnum_buf`, upstream 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
- Found by: Frama-C WP with `-warn-signed-downcast`: the proof of `tv_get_lnum_buf` fails exactly
  on the cast (`typval/wp_lnum`, upstream 18/20, the two open goals are `rte_signed_downcast`).
- Fix: verified_neovim branch `claude/project-thread-9w9zko`, commit 1155cbc; the fixed
  `tv_get_lnum_buf` and the new `tv_number_to_lnum` prove fully (20/20, 8/8).
- Status: not reproduced in a running Neovim yet (this session could not download a release
  build); the conversion itself is shown by `lnum-wraps-repro.c`. Upstream issue not filed.

## What happens

```c
linenr_T lnum = (linenr_T)tv_get_number_chk(tv, NULL);   // tv_get_lnum
return (linenr_T)tv_get_number_chk(tv, NULL);            // tv_get_lnum_buf
```

A Vimscript Number is 64-bit; `linenr_T` is `int32_t`. The conversion of a value outside
int32 is implementation-defined; GCC and Clang keep the low 32 bits. So the Number
4294967297 (2^32 + 1) becomes line 1 and 4294967301 becomes line 5:

    Number 4294967297 -> line 1
    Number 4294967301 -> line 5
    Number -4294967295 -> line 1
    Number 2147483648 -> line -2147483648

There are 23 callers of `tv_get_lnum` and 7 of `tv_get_lnum_buf`, among them
`setline()`, `setbufline()`, `deletebufline()`, `getline()`, `getbufline()`, `indent()`,
`foldlevel()`. Expected (by code reading, to be confirmed in a build):
`:call setline(4294967297, 'x')` replaces line 1 instead of failing as for any line past
the end, and `:call deletebufline('%', 4294967297)` deletes line 1. In Vim `linenr_T` is
`long`, 64-bit on Linux/macOS, so Vim does not wrap there; this is Neovim-specific.

## Fix

Clamp instead of wrap (`tv_number_to_lnum`): above `MAXLNUM` gives `MAXLNUM` (past any
buffer end, so callers report "invalid line" as they already do for large values),
below `INT32_MIN` gives `INT32_MIN` (still <= 0, invalid). Values in int32 range are
unchanged, so nothing else changes.

Proof: `bash libraries/neovim/typval/wp_lnum/run_wp.sh <upstream tree> <fixed tree>`.
