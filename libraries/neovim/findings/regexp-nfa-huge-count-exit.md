# regexp NFA engine: a large \{n,m} count makes Neovim exit (out of memory)

**File:** `src/nvim/regexp.c`, `nfa_regpiece`, `nfa_regcomp`, `nfa_regmatch` (commit 7b87ce8).
**Found by:** libFuzzer (`../regexp_search/fuzz/fuzz_regexp.c`, out-of-memory reports).
**Fix:** not yet; needs a decision on the limit (below).

## What goes wrong

The NFA compiler expands `x\{n,m}` into m copies of `x`. With the automatic engine it bails
out to the backtracking engine when `m > 500` or `m > n + 200`, but when the NFA engine is
requested (`\%#=2` or `'regexpengine'=2`) there is no limit:

```
:echo match('xx', '\%#=2x\{3,15555555}')
E41: Out of memory!
Nvim: Finished.          (exit code 1)
```

`nfa_regcomp` asks for `nstate * sizeof(nfa_state_T)` bytes (about 12 GB here) with `xmalloc`,
which exits Neovim when the allocation fails; nested counts grow the postfix array the same way
first, and `nfa_regmatch` allocates two more lists of `nstate + 1` entries per call. On a
system with overcommit the allocation may succeed and the process is killed while filling it.

A 20-byte pattern therefore ends the editor session. Patterns come from users, but also from
plugins, `:syntax` files, LSP servers and `vim.regex()` calls with untrusted input.

Reproducer: `regexp-nfa-huge-count-exit-repro.lua` (exits Neovim; run it in a throwaway shell).

## Possible fixes (decision needed)

1. Count the states before allocating and fail with `E363: Pattern uses more memory than
   'maxmempattern'` when `nstate * sizeof(nfa_state_T)` or the postfix size exceeds
   `'maxmempattern'`. Consistent with the option's documented meaning, but the default (1000 KiB)
   would also reject some patterns that work today with an explicit `\%#=2`.
2. Use `try_malloc` and report an error instead of exiting. Small change, but with overcommit
   the process can still be killed later.
3. Apply the automatic engine's bail-out (fall back to backtracking) even when NFA was asked for.

## Severity

Medium: denial of service (editor exit, unsaved work lost unless swap files recover it) from
a short pattern, when the NFA engine is requested explicitly.
