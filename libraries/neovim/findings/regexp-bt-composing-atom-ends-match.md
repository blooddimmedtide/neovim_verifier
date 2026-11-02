# regexp backtracking engine: a composing-character atom ends the whole match

**File:** `src/nvim/regexp.c`, `regmatch`, case `MULTIBYTECODE` (commit 7b87ce8). Vim's
`regexp_bt.c` has the same code.
**Found by:** the backtracking-vs-NFA differential in `../regexp_search/fuzz/fuzz_regexp.c`.
**Fix:** not yet. A first fix (continue instead of `RA_MATCH`) broke Vim's own test
`Test_multibyte_chars` (pattern of two composing chars), so the fix needs the pattern side
redesigned; see below.

## What goes wrong

When the operand of a `MULTIBYTECODE` node is a lone composing character and that character
is found at the current position, the code sets `status = RA_MATCH`. In `regmatch`,
`RA_MATCH` means "the whole regexp matched", so every node after this one is skipped.

| Pattern (`\%#=1`) | Text | Backtracking | NFA |
|---|---|---|---|
| `<U+0301>q` | `a<U+0301>~` | `á` (the `q` is never tried) | no match |
| `<U+0301>x` | `a<U+0301>~` | `á` | no match |
| `\(<U+0301>x\)` | `a<U+0301>~xyz` | match, `\1` empty (group never closed) | no match |

`:s` with the third pattern replaces `á` with an empty `\1`.

Reproducer: `regexp-bt-composing-atom-repro.lua`.

## Why the obvious fix is not enough

The early `RA_MATCH` also hides a second problem: the backtracking compiler emits one
`MULTIBYTECODE` node per composing character, while the matcher consumes the base character
and all its composing characters at the first node. For the pattern `<U+05B9><U+05BB>` the
second node then has nothing left to match; the early `RA_MATCH` makes the test pass by
accident. A correct fix has to put the whole run of composing characters into one operand
(as `EXACTLY` and the NFA engine do) and check each of them, then continue matching.

## Severity

Low: wrong matches and wrong `:s` results for patterns that start a piece with a composing
character, only with the backtracking engine (used for `'regexpengine'=1`, and by the default
engine for patterns the NFA engine can't handle).
