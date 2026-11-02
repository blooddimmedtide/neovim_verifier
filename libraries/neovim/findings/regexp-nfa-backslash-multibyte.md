# regexp NFA engine: a backslash before a multibyte character breaks the pattern

**File:** `src/nvim/regexp.c`, `nfa_regatom` (commit 7b87ce8).
**Found by:** the backtracking-vs-NFA differential in `../regexp_search/fuzz/fuzz_regexp.c`.
**Fix:** `blooddimmedtide/verified_neovim`, branch `claude/project-thread-legcap`, commit
`dd5213f`. Not yet machine-proved (needs a spec of the NFA compiler); checked by the
differential fuzzer and Neovim's own regexp tests.

## What goes wrong

`peekchr()` treats a backslash before a character that can never be magic as nothing, so
`\é` means `é` (the backtracking engine matches `é` with it). In `nfa_regatom` the default case
measures the character with `utfc_ptr2len(old_regparse)`, but `old_regparse` still points at
the backslash, so the length is 1. Because that differs from `utf_char2len('é')`, the code
takes the "base character plus composing characters" branch, emits a composing atom for `é`
and sets `regparse = old_regparse + 1`, which is back on the `é`. The pattern compiles to
"composing atom é, then é" and never matches.

| Pattern | Text | Backtracking | NFA (upstream) | NFA (fixed) |
|---|---|---|---|---|
| `\é` | `é` | `é` at 0 | no match | `é` at 0 |
| `x\éy` | `xéy` | `xéy` at 0 | no match | `xéy` at 0 |
| `\😀S7` | ` +😀S7` | match at 2 | no match | match at 2 |

The default `'regexpengine'` (0) tries the NFA engine first, so `/\é` finds nothing in normal use.

Reproducer: `regexp-nfa-backslash-multibyte-repro.lua`.

## Fix

Skip the backslash before measuring when the character is non-ASCII (`c >= 0x80` here is
always a literal character; magic characters are negative).

## Severity

Low: wrong search results for an unusual pattern spelling.
