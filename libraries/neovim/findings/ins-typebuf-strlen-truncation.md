# ins_typebuf: (int)strlen() truncation, segfault on a 2 GiB typeahead string

**File:** src/nvim/input.c (formerly getchar.c), `ins_typebuf()`, upstream 7b87ce822e6f.
**Found by:** Frama-C WP (-wp-rte), the `requires n <= INT_MAX - 5 * (MAXMAPLEN + 4)` the
upstream proof needs. **Reproduced** in Neovim 0.9.5 (Ubuntu 24.04 package, same code).

```c
int addlen = (int)strlen(str);
```

For a string of 2^31 bytes or more, `addlen` is negative (2^31 gives INT_MIN). With
`offset == 0` the "easy case" `addlen <= typebuf.tb_off` is true, `tb_off -= addlen`
overflows, and `memmove(..., (size_t)addlen)` copies about 2^64 - 2^31 bytes: segfault.
Strings a bit shorter than 2^31 also overflow `extra = addlen + newoff + 4 * (MAXMAPLEN + 4)`
(signed overflow) in the reallocation branch.

Reachable from `feedkeys()` and `nvim_feedkeys()` (and :normal, registers, mappings with
very long right-hand sides).

## Reproducer

`typebuf/repro/feedkeys_2gib.vim` (needs about 5 GB of RAM):

```
nvim --headless --clean -u NONE -S feedkeys_2gib.vim   # prints 2147483648, then exit 139 (SIGSEGV)
```

## Fix

verified_neovim branch `claude/project-thread-2h2bgy`, commit 4c11bf5: reject strings longer
than `INT_MAX - 5 * (MAXMAPLEN + 4)` with E74 "Command too complex", the error the existing
too-long check already gives. The fixed function is proved with the same contract minus the
length precondition (behavior `too_long` covers the new case).
