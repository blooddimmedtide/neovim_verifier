# cmdhist.c: calc_hist_idx(type, INT_MIN) negates INT_MIN and reads far out of bounds

**Function:** `calc_hist_idx` in `src/nvim/cmdhist.c` (pinned commit in `../cmdhist/cbmc/PINS`).
**Reached from:** Vimscript `histget({hist}, -2147483648)` and `histdel({hist}, -2147483648)`
(`tv_get_number` returns the 64-bit number, which is cast to `int`), whenever that history has
at least one entry.

## What goes wrong

```c
} else if (-num <= hislen) {   // num == INT_MIN: signed overflow (undefined behaviour)
  i += num + 1;                // i = hisidx - 2147483647
  if (i < 0) { i += hislen; }  // still about -2^31
  if (hist[i].hisstr != NULL)  // read ~2^31 entries before the array
```

With wrapping arithmetic `-INT_MIN == INT_MIN`, so the range check passes and `hist[i]` is read
about 2^31 * sizeof(histentry_T) bytes before the history table. Found by CBMC
(`--signed-overflow-check`, `--bounds-check`) on the harness in `../cmdhist/cbmc/`.

## Reproducer

`cmdhist-calc-hist-idx-int-min/repro.c` (verbatim function body). Results here:

- `gcc -O0 -fsanitize=undefined,address`: "negation of -2147483648 cannot be represented in
  type 'int'", then AddressSanitizer SEGV.
- `gcc -O2` (no sanitizers): segmentation fault.

Not yet tried in a built Neovim: `:echo histget('cmd', -2147483648)` after one `:` command
should crash or return a wrong entry. Treat that as unconfirmed until run.

## Fix (one line)

```diff
-  } else if (-num <= hislen) {
+  } else if (num >= -hislen) {
```

`hislen` is in `[0, INT_MAX]`, so `-hislen` never overflows. The fixed function is proved
against the same reference (see CLAIM.md). Upstream issue: draft only, not filed (owner files).
