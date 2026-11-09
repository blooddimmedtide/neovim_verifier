---
entry: neovim/src/nvim/window.c (window-size arithmetic subset)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
toolchain: CBMC 6.4.1 (.deb, see tools/install.sh), CaDiCaL back end
strength: candidate   # partial: 4 of 193 window.c functions; no review or mutants yet
platform: x86_64, signed and unsigned char
---

# Claim card: Neovim src/nvim/window.c (in progress)

| Function | Property, for every input | Status |
|---|---|---|
| `win_default_scroll(wp)` | `max(w_view_height / 2, 1)` per `:help 'scroll'`; no overflow | proved |
| `frame_check_height(fr, h)` | true iff `fr->fr_height == h` and, for an `FR_ROW` frame, every child's height is `h` | proved (up to 4 children) |
| `frame_check_width(fr, w)` | the same for widths and `FR_COL` frames | proved (up to 4 children) |
| `global_stl_height()` | 1 when `'laststatus'` is 3, else 0, for every 64-bit option value | proved |
| `set_fraction(wp)` | for `h > 1` rows: `floor((wrow + 1/2) * 16384 / h)`, in `[0, 16384)` (0 is reachable: with `h > 8192` and `wrow = 0` the fraction truncates to 0); unchanged for `h <= 1` | not finished (CBMC run on the non-linear division did not finish before the 09:00 UTC stop) |

## What the proof relies on

1. CBMC is sound for this code (bit-precise integers).
2. Extraction: exact upstream text of each function (sha256 pinned in `cbmc/build.py`). The
   prelude declares only the struct fields these functions use, each line checked against
   `buffer_defs.h`, `window.h`, `globals.h`, `macros_defs.h`, `types_defs.h`, `option_vars.h`.
   Field order differs from upstream; these functions use fields by name only.
3. `frame_check_*`: child lists of length 0..4, every field nondeterministic, unwinding
   assertions on. Longer lists are not covered (a WP loop invariant would close this).
4. `set_fraction` harness preconditions: `0 <= w_wrow < w_view_height` (the cursor is inside the
   window) and `w_view_height <= 131071`; neither is asserted by the function, so both must be
   justified before the claim can stand. `w_wrow * 16384` overflows an `int` from `w_wrow >= 131072`.

## Not done (this is not a finished claim)

- No adversarial review, no differential test, no CI run yet. Four quick hand-made mutants
  (one per proved function: wrong layout, wrong field, wrong minimum, `>=` for `==`) were all caught;
  this is not the 10-mutant review the prompt requires.
- 189 other window.c functions are unverified (see STATUS.md); the layout functions
  (`frame_new_height`, `frame_minheight`, `win_equal_rec`, `frame_setheight`, ...) depend on
  global window state and need a frame-tree model.

## Evidence

| Check | Command | Result |
|---|---|---|
| CBMC, signed char | `bash window/cbmc/run_cbmc.sh <neovim>` | 4/4 proved (set_fraction pending) |
| CBMC, unsigned char | same script, `--unsigned-char` | 4/4 proved (set_fraction pending) |
