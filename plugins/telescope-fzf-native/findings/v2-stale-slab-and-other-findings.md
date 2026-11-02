# telescope-fzf-native: findings from the proof of the fixed src/fzf.c

Upstream nvim-telescope/telescope-fzf-native.nvim b25b749 (all items are also in the
copy with the two out-of-bounds fixes, `../findings/fix.diff`). None of these is a
memory-safety bug; the proof found no further UB in the fixed file (see `../CLAIM.md`).

## 1. Highlight positions depend on earlier calls (stale slab memory) — functional bug

`fzf_fuzzy_match_v2` takes its score matrices from the caller's slab and does not clear
them. Phase 3 writes row `i` of the consecutive-count matrix `C` only from column
`F[i] - f0`, but the backtrace (Phase 4) reads
`c.data[ii + width + j0 + 1]` (row `i + 1`, column `j + 1`) for every `j` it walks
through, also left of `F[i + 1]`, where the row holds whatever an earlier call left. The
value feeds `prefer_match`, which picks between equal-score paths, so the returned
positions (and `start`) depend on the history of the slab. The score and `end` do not
(CBMC `h_v2_slab_independent` on the fixed copy: "same score and end" and "same number of
positions" proved, "same start" and "same positions" fail, for text <= 5 and pattern <= 3;
difftest: 1,176 differing cases in 2,000,000 runs, none with a different score).

Reachable in normal use: Telescope's sorter scores every line with one slab
(`fzf_get_score`) and then asks `fzf_get_positions` for the highlights with the same slab.

Reproducer (`repro_v2_slab.c`, fixed and upstream file alike):

```
fresh slab:                  6 3 1
after scoring another line:  6 3 2
DIFFERENT positions for the same text and pattern
```
(text `bcc_abc`, pattern `c_c`; the earlier line is `cc_bb_b_   ` with pattern `__`).

Fix (`fix-v2-stale-slab.diff`): zero `C` after allocating it (`memset`), which is what a
fresh slab or a `NULL` slab already gives. A zero means "no consecutive match here", which
is the right value for those cells (row `i + 1` cannot match left of `F[i + 1]`).
With the fix, CBMC proves `h_v2_slab_independent` (result and positions identical with a
slab of arbitrary contents and with no slab) for the bound, and the differential test
finds 0 differing cases in 200,000 runs.

Found by: CBMC `h_v2_slab_independent` (counterexample) and `difftest` (counted).
fzf 0.27.0's Go code (`src/algo/algo.go`, the version this file ports) has the same read
(`C[I+width+j0+1]` in Phase 4, `C` filled only from `F[i]` on in Phase 3), so this is
inherited; whether later fzf versions changed it was not checked.

## 2. A matching line can get a score <= 0 (long lines) — integration bug

When `text length * pattern length` exceeds the slab (102,400 for the default slab), v2
falls back to `fzf_fuzzy_match_v1`, whose score is not clamped at 0: a long gap costs
more than the matches earn. `fzf_get_score` then returns a negative (or zero) score for a
line that matches. The plugin's sorter (`lua/telescope/_extensions/fzf.lua`) treats 0 as
"filtered" and returns `1 / score` otherwise; Telescope ranks smaller values first, so a
negative score puts the line above every real match (and a score of exactly 0 hides a
matching line).

Reproducer (`repro_negative_score.c`): a 60,000-byte line `a` + 60 × `x` + `b` + `x…`
with pattern `ab` gives `score -14`, positions returned.

Reachable with long lines (minified files in `live_grep`, long `find_files` paths are
not long enough). The same unclamped score breaks the only-inverse path of
`fzf_get_score` (`final += score; return final > 0 ? 0 : 1`): with pattern `!ab`, a long
line that contains the match with score <= 0 counts as "no match" and is kept. Fix suggestion: clamp the score of a match to at least 1 in
`fzf_get_score` (or in the Lua sorter).

## 3. A line that matches only through an inverse term of an OR group is hidden — integration bug

`fzf_get_score` gives an AND-set that is satisfied by an inverse term (`!a` does not match)
the score 0, the same as fzf 0.27.0 (`pattern.go`, `extendedMatch`). fzf then keeps every
item for which all sets matched, whatever the score (`MatchItem`: `len(offsets) ==
len(p.termSets)`). The port uses 0 to mean "no match": the Telescope sorter returns -1
(filtered) for `score == 0`. The port handles this only for patterns made entirely of
single inverse terms (`only_inv`: returns 1). If any set is an OR group that is satisfied by
an inverse term, and no other set adds a positive score, a matching line gets 0 and is
hidden. `fzf_get_positions` says it matches.

Reproducer (`repro_inverse_or.c`, fixed and upstream file alike):

```
pattern !a | b   line "c": score 0, positions returned (it matches)
pattern !a | !b  line "c": score 0, positions returned (it matches)
```

So `!a | !b` hides every line, and `!test | foo` hides lines without "test" unless they
contain "foo". Fix suggestion: when every set matched, return `max(total, 1)`. That also
covers the `only_inv` case and the non-positive v1 scores of finding 2. The CBMC/difftest
composition oracle states the code's rule (sum of the sets' scores, 0 if a set fails), so it
does not flag this. The finding came from reading the composition against fzf's `pattern.go`.

## 4. Smaller deviations (documented in the spec, not fixed)

- `trim_whitespace_left` skips at most half of the leading spaces
  (`trim-whitespace-left.md`); not observable through `fzf_parse_pattern` (proved).
- A TAB character typed in the pattern searches for a space: the parser marks `\ ` with
  TAB and then turns every TAB of a token into a space. fzf keeps a TAB literal.
- `fzf_equal_match` (`^foo$`) strips the text's leading/trailing whitespace even when the
  pattern itself starts/ends with a space (`^\ a$` never matches ` a`); fzf 0.27.0's
  `EqualMatch` skips the strip in that case (`fzf_prefix_match` / `fzf_suffix_match` here do).
- `fzf_fuzzy_match_v2` with `pos == NULL` returns `start = end - 1` (fzf 0.27.0: `F[0]`, the
  first occurrence of the first pattern byte). No caller in the plugin uses `start` then.
- `is_ascii` is stubbed to `true`, so pattern bytes >= 0x80 are matched as raw bytes (fzf
  works on runes). A design choice of the port; noted for completeness.
- `str_replace_char(s, c, c)` never terminates (only call: `'\t'` -> `' '`).
- `malloc`/`realloc` results are never checked (`fzf_pos_array`, `fzf_make_slab`,
  `str_tolower`, `fzf_parse_pattern`, `alloc16/32`, ...): out of memory is a NULL write.
- Case folding and whitespace use the process locale (`tolower`, `isspace`); the proof
  assumes a locale that classifies bytes like "C" (all glibc UTF-8 locales). In a Latin-1
  locale `str_tolower` folds bytes >= 0x80 but v2's search does not, so such patterns
  never match.
