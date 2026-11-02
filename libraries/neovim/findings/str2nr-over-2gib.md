# vim_str2nr: negative length and int overflow on numbers of 2 GiB characters or more

**File:** `src/nvim/charset.c`, `vim_str2nr` (commit 7b87ce8).
**Found by:** the Frama-C WP proof in `../charset/wp/` (the `-wp-rte` goals for `*len = (int)(ptr - start)` and the octal check's `i++` fail without a length limit).
**Fix:** `blooddimmedtide/verified_neovim`, branch `claude/project-thread-yx7abl` (commit 213eb11), proved for every input.

## What goes wrong

With `maxlen == 0` (no limit; most callers) the scan has no bound:

```c
#define STRING_ENDED(ptr) \
  (!(maxlen == 0 || (int)((ptr) - start) < maxlen))
...
    for (int i = 2; !STRING_ENDED(ptr + i) && ascii_isdigit(ptr[i]); i++) {   // old-style octal check
...
    *len = (int)(ptr - start);
```

| Input (maxlen 0) | Effect |
|---|---|
| a number of `2^31 + k` characters (k < 2^31) | `*len` is negative (`-2^31 + k`) |
| a number of `2^32 + k` characters | `*len` is `k`: too short |
| `"0"` followed by 2^31 or more octal digits, `STR2NR_OCT` allowed | `i++` overflows `int`: undefined behavior |

Reproducer: `str2nr-over-2gib-repro.c`. With UBSan, upstream prints `len=-2147483632` for
2^31 + 16 decimal digits and reports `signed integer overflow: 2147483647 + 1` for the
octal case; the fixed version prints `len=2147483647` for both.

## Reachability

`eval_number()` (eval.c) parses every number literal in Vimscript with
`vim_str2nr(*arg, NULL, &len, STR2NR_ALL, &n, NULL, 0, true, NULL)` and then does
`*arg += len`. A literal of 2^31 + k digits (for example from `:execute` on a string built with
`repeat()`, or a sourced file with such a line) moves the parse pointer about 2 GiB *backwards*,
before the start of the buffer; the next read is out of bounds. The octal overflow is reached
the same way with a literal `0777...`. Other callers with `maxlen == 0`: `ex_getln.c`,
`option.c`, `typval.c` (`tv_get_number`), `keycodes.c`, `strings.c` (`str2nr()`).

Not tried end to end in a Neovim build (it needs a 2 GiB string); the function-level
reproducer shows both defects.

## Fix

Stop the scan at `INT_MAX` characters when no `maxlen` is given, and compare without the
`int` cast:

```c
#define STRING_ENDED(ptr) \
  (!(maxlen == 0 ? (ptr) - start < INT_MAX : (ptr) - start < maxlen))
```

`*len` then never exceeds `INT_MAX`, and the octal loop's `i` stays below `INT_MAX`. A number
that long already saturates (`UVARNUMBER_MAX`, overflow flag set), so no valid result changes.
The fixed function is proved by `../charset/wp/run_wp.sh <fixed checkout> 120 --fixed vim_str2nr`
for every input with no length precondition.

## Severity

Low: it needs a single number of 2 GiB characters. Out-of-bounds read in `eval_number`'s
caller, no write found.

## Observations (not bugs, recorded in the claim card)

- With both `nptr` and `unptr` given, a positive value above `VARNUMBER_MAX` is clamped in
  `*unptr` too (the code clamps `un` before storing it). No caller passes both.
- `"-9223372036854775808"` gives `VARNUMBER_MIN` but also sets `*overflow` (the magnitude
  exceeds `VARNUMBER_MAX`).
