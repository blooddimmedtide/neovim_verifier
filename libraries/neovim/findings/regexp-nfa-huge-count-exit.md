# regexp NFA engine: a large \{n,m} count makes Neovim exit (out of memory)

**File:** `src/nvim/regexp.c`, `nfa_regpiece`, `nfa_regcomp`, `nfa_regmatch` (commit 7b87ce8).
**Found by:** libFuzzer (`../regexp_search/fuzz/fuzz_regexp.c`, out-of-memory reports).
**Fix:** `blooddimmedtide/verified_neovim`, branch `claude/project-thread-legcap`, commit
`b5ad208` (option 3 below, chosen by the owner on 2026-11-02). Not machine-proved yet (needs
an NFA compiler spec); checked by Neovim's regexp tests and a new regression test.

## What goes wrong

The NFA compiler expands `x\{n,m}` into m copies of `x`. With the automatic engine it bails
out to the backtracking engine when `m > 500` or `m > n + 200`, but only when `n < 200`, so
the default engine also runs out of memory on `x\{300,15555555}`. When the NFA engine is
requested (`\%#=2` or `'regexpengine'=2`) there is no limit at all:

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

## Fix

Before expanding a count, `nfa_regpiece` estimates the postfix size (copies x (atom length + 2)).
Above 16M items (about twice the largest pattern in Neovim's tests, which takes ~440 MB) it
fails with `nfa_too_big` set, and `vim_regcomp` compiles the pattern with the backtracking
engine, also when the NFA engine was requested. The automatic engine's existing heuristic is
unchanged, so every pattern that compiled before still uses the same engine.

Remaining limitation: patterns that need the NFA engine (`[[:upper:]]`/`[[:lower:]]` with
characters above 255) get the backtracking engine's behavior for those classes when they are
this large, instead of exiting.

## Options that were considered

1. Count the states before allocating and fail with `E363: Pattern uses more memory than
   'maxmempattern'` when `nstate * sizeof(nfa_state_T)` or the postfix size exceeds
   `'maxmempattern'`. Consistent with the option's documented meaning, but the default (1000 KiB)
   would also reject some patterns that work today with an explicit `\%#=2`.
2. Use `try_malloc` and report an error instead of exiting. Small change, but with overcommit
   the process can still be killed later.
3. Apply the automatic engine's bail-out (fall back to backtracking) even when NFA was asked for.

## Severity

Medium: denial of service (editor exit, unsaved work lost unless swap files recover it) from
a short pattern, with the default engine too.
