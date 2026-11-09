# check_regexp_delim: negative argument to isalpha() (undefined behavior)

Pinned commit 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd, src/nvim/ex_cmds.c.

`do_sub()` and `ex_global()` call `check_regexp_delim(*cmd)`, where `cmd` is `char *`, and
`check_regexp_delim` calls `isalpha(c)`. On platforms where `char` is signed (x86_64 Linux,
Windows), a delimiter byte >= 0x80 (for example the first byte of `:s€a€b€` or `:g€x€d`) becomes a
negative `int` other than `EOF`. C11 7.4p1 makes that undefined behavior.

Severity: low. glibc's table accepts -128..-1 and musl's `isalpha` masks the value, so on those
there is no crash; the MSVC debug runtime asserts on it, and other C libraries may index out of
their table. No runtime reproducer was built (glibc does not trap); the evidence is the CBMC
counterexample of `ex_cmds/cbmc/harness_delim.c` `h_call_sites` with signed char.

Fix (verified_neovim branch `fix-check-regexp-delim-signed-char`, 42c2ba8): pass
`(uint8_t)(*cmd)` at both call sites, as the neighbouring `vim_strchr` calls already do. Proved by
`bash ex_cmds/cbmc/run_delim.sh <fork checkout>` for both signednesses.

Upstream issue draft (not filed; the owner files it):

> **check_regexp_delim() passes a negative char to isalpha()**
> In src/nvim/ex_cmds.c, do_sub() and ex_global() call `check_regexp_delim(*cmd)` with a plain
> `char`. With signed char, a non-ASCII delimiter byte becomes negative, and `isalpha()` on a value
> that is neither EOF nor representable as unsigned char is undefined behavior (C11 7.4p1).
> Suggested fix: `check_regexp_delim((uint8_t)(*cmd))` at both call sites.
