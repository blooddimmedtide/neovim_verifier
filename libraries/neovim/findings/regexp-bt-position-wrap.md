# regexp backtracking engine: \%Nl, \%Nc, \%Nv numbers wrap around at 2^32

**File:** `src/nvim/regexp.c`, `regatom` (backtracking engine, commit 7b87ce8).
**Found by:** review while proving the number readers (the NFA engine checks this; the
backtracking engine does not).
**Fix:** `blooddimmedtide/verified_neovim`, branch `claude/project-thread-legcap`, commit
`b2bbb00`. Not yet machine-proved (the number loop is inline in `regatom`).

## What goes wrong

```c
uint32_t n = 0;
while (ascii_isdigit(c)) {
  n = n * 10 + (uint32_t)(c - '0');   // wraps silently
```

`\%4294967297l` is read as `\%1l` and matches line 1. The NFA engine gives
`E951: \% value too large` for the same pattern. With the default engine the NFA error is
shown, so the wrong match needs `'regexpengine'=1` or `\%#=1`.

Reproducer: `regexp-bt-position-wrap-repro.lua`.

## Fix

Give E951 when the next digit would wrap the `uint32_t`. Every number that fits keeps its
meaning (the backtracking engine still accepts numbers between 2^31 and 2^32 - 1, which the NFA
engine rejects; that difference is older and left alone).

## Severity

Low: wrong match for an out-of-range pattern number.
