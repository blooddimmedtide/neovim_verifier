# regexp: engines disagree on a composing character at the start of the text

**File:** `src/nvim/regexp.c` (NFA matching of composing characters, commit 7b87ce8).
**Found by:** the backtracking-vs-NFA differential.
**Status:** open; which engine is right needs the spec (`:help patterns-composing`).

When the text starts with a composing character that has no base character (a lone U+0301),
the backtracking engine matches the pattern `<U+0301>` there and the NFA engine finds no
match. `:help patterns-composing` says a pattern that starts with a composing character
matches "any character including this composing character"; a lone composing character is a
character of its own for `utfc_ptr2len`, so the backtracking result looks right.

| Pattern | Text | Backtracking | NFA |
|---|---|---|---|
| `<U+0301>` | `<U+0301>~` | match at 0 | no match |
| `<U+0301>` | `<U+0301>x` | match at 0 | no match |

The differential fuzzer skips patterns with composing characters (`FUZZ_SKIP_COMPOSING=1`)
until this and `regexp-bt-composing-atom-ends-match.md` are settled.
