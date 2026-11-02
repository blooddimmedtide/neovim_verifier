# regexp getdecchrs: signed overflow on long digit runs in a pattern

**File:** `src/nvim/regexp.c`, `getdecchrs` (commit 7b87ce8); callers `\%d`, `\@N<=`/`\@N<!`
(both engines) and `[\d...]` collections.
**Found by:** libFuzzer + UBSan (`../regexp_search/fuzz/fuzz_regexp.c`), then the WP proof
(`../regexp/wp`), which only goes through with the precondition below.
**Fix:** `blooddimmedtide/verified_neovim`, branch `claude/project-thread-legcap`, commit
`3336e2d` (`fix(regexp): no overflow on long digit runs in patterns`). `getdecchrs` itself is proved for every input; the two caller changes
in the same commit are reviewed by hand and tested, not proved.

## What goes wrong

```c
for (i = 0;; i++) {
  ...
  nr *= 10;          // int64_t nr: overflows after 19 digits
  nr += c - '0';
```

- 19 or more digits overflow `int64_t nr` (undefined behavior; UBSan:
  `regexp.c:1131: signed integer overflow: 1844674407370955168 * 10`).
- The `int i` counter overflows on a run of 2^31 digits (undefined behavior), even when the
  value is small (leading zeros).
- With wrapping arithmetic the value is taken mod 2^64: `\%d18446744073709551681` matches `A`
  instead of giving E678.
- `\@N<=` limits were then cut to 32 bits (backtracking engine, `(uint32_t)nr`) or to `int`
  (NFA engine, `(int)c2`): `\@4294967297<=` limited look-behind to 1 byte.

Reproducer: `regexp-getdecchrs-overflow-repro.lua` (`nvim --clean -l`; a UBSan build reports the
overflow, any build shows `\%d18446744073709551681` matching `A`).

## Fix

`getdecchrs` stops multiplying once the value passes `INT_MAX` and returns `INT_MAX + 1` for
any larger number (every caller already rejects or clamps values above `INT_MAX`); "no digits"
is detected by comparing `regparse` with its start instead of counting. A look-behind limit
above `INT_MAX` means no limit in both engines. Values up to `INT_MAX` behave as before.

Proved with Frama-C WP (`../regexp/wp/run_wp.sh`): the fixed function returns `-1` and
consumes nothing when no digit follows, otherwise consumes exactly the digit run and returns
`min(value, INT_MAX + 1)`, for every run length. The upstream function is proved to return the
exact value only under `run length <= INT_MAX && value <= INT64_MAX`.

## Severity

Low: undefined behavior from a pattern with a 19-digit number; in practice wrong numbers, not
memory errors.
