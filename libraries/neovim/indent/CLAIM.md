---
entry: neovim/src/nvim/indent.c (tabstop arithmetic helpers)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
toolchain: CBMC 6.4.1 (.deb, see tools/install.sh)
strength: candidate   # bounded in the 'vartabstop' list length; owner sign-off pending
tools: CBMC 6.4.1 (bit-precise bounded model checking; every loop fully unwound, proved by unwinding assertions)
platform: x86_64, char signed and unsigned (both run)
---

# Claim card: Neovim indent.c tabstop helpers (work in progress)

## Spec (cbmc/spec.h, written from :help 'vartabstop', not from the code)

With widths w1..wn (n >= 1) the tab stops are 0, w1, w1+w2, ..., Sn = w1+...+wn, and after
Sn one stop every wn columns. Plain 'tabstop' ts is the layout n = 1, w1 = ts. For a column c,
`prev(c)` is the last stop <= c, `next(c)` the first stop > c, `idx(c)` the number of stops in (0, c].
The reference uses 64-bit arithmetic.

| Function | Property (for every col in [0, INT_MAX]) |
|---|---|
| `tabstop_padding(col, ts, vts)` | `next(col) - col`; ts = 0 means 8 |
| `tabstop_at(col, ts, vts, left)` | right: `next(col) - prev(col)`; left: width of the interval ending at `prev(col)`, or, when col is in the first interval, a value >= col (the function documents that any such value works; it returns col, so 0 at col 0) |
| `tabstop_start(col, ts, vts)` | `prev(col)` |
| `tabstop_fromto(s, e, ts, vts, &tabs, &spaces)` | for s <= e: if `next(s) > e`, (0, e - s); else (`idx(e) - idx(s)`, `e - prev(e)`); ts = 0 means curbuf's 'tabstop' |
| `tabstop_copy(vts)` | NULL for NULL; else a fresh exact-size array equal to vts |
| `tabstop_count(vts)` / `tabstop_first(vts)` | `vts[0]` or 0; `vts[1]` or 8 |

All runs also check no out-of-bounds access, no signed overflow, no division by zero, no
lossy conversion (`--conversion-check`), with exact-size arrays.

## Input preconditions (each from the caller contract)

- Widths and ts in [1, TABSTOP_MAX = 9999]: `tabstop_set` rejects `n <= 0 || n > TABSTOP_MAX`,
  and the 'tabstop' option check enforces the same range.
- vts is NULL, `{0}`, or an exact-size array `{n, w1..wn}` as `tabstop_set` builds it.
- `tabstop_first` with a non-NULL list needs n >= 1 (it reads `vts[1]`); `tabstop_set` never
  builds a count-0 list (it returns NULL for "" and "0").
- `tabstop_fromto`: start_col <= end_col (callers pass a start before the end).
- Bound: n <= 3 entries (MAXN in harness.c). Not yet proved for longer lists; an unbounded
  proof (WP) is still open.

## Run results (08:51 UTC 2026-11-09, CBMC 6.4.1, x86_64, signed + unsigned char)

| Harness | Result |
|---|---|
| h_at (tabstop_at) | proved |
| h_copy_count_first (tabstop_copy, tabstop_count, tabstop_first) | proved |
| h_padding, h_start, h_fromto | did not finish before the 09:00 stop (64-bit division in the reference is slow for CBMC); still open |

No finding so far. The only spec change during the work: tabstop_at(left) in the first
interval returns col, so 0 at col 0; the harness first asked for r > 0, which is not documented,
and now asks for r >= col.

Still missing for these: differential test, adversarial review with mutants, CI run.

## Not yet covered

The other 32 functions of indent.c, and `tabstop_set` (string parsing; calls getdigits/atoi/opt_error).
See status.tsv for the per-function list.
