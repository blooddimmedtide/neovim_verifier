# Claim: src/nvim/cmdhist.c ring-buffer index functions (bounded, work in progress)

Source: `blooddimmedtide/verified_neovim` at the commit and sha256 in `cbmc/PINS`.
Fix: branch `claude/project-thread-anveif` of `verified_neovim` (commit 0c9c0ba, one line).
Tool: CBMC 6.4.1, `--bounds-check --pointer-check --signed-overflow-check --unwinding-assertions`.
Run: `cd cbmc && bash run.sh` (upstream) and `bash run.sh -DFIXED -DCHECK_CHAR -DCHECK_IDX -DCHECK_DEL`.

**Strength: bounded model check, not a full proof.** The history table size `hislen` is checked
for every value 0..4 only (real `'history'` allows up to 10000). Every other input (history type,
`num`, `hisidx`, entry ids, number of filled entries) is fully nondeterministic.

## Results

| Function | Property | Upstream | Fixed |
|---|---|---|---|
| hist_char2type | documented char -> type map, all `int` inputs | pass | pass |
| get_history_idx | id of newest entry, or -1 when empty / bad type | pass | pass |
| calc_hist_idx | equals a reference written from its doc comment; no OOB, no overflow | **FAIL** (num = INT_MIN) | pass |
| del_history_idx | returns true iff the entry exists; removes exactly one filled entry; hisidx stays in range; memory safe | fails through calc_hist_idx | pass |

Finding: `../findings/cmdhist-calc-hist-idx-int-min.md` (`histget('cmd', -2147483648)` negates
INT_MIN and reads ~2^31 entries before the table; ASan SEGV and plain -O2 segfault reproduced).

## Assumptions (harness preconditions)

- Ring-buffer invariant kept by the rest of cmdhist.c: `-1 <= hisidx < hislen`; filled entries are
  the newest `filled` slots going backwards from `hisidx`, with strictly decreasing ids >= 1;
  empty slots have `hisstr == NULL`. Not yet proved to be preserved by add_to_history etc.
- `xmalloc` never returns NULL. `hist_free_entry` is modelled as clearing the entry (free not modelled).
- Only one history type is populated per run; the others are NULL tables (all are reached via `t`).

## Gaps (not done yet)

- Planted-bug check (6 quick mutants): 5/6 caught. **Not caught:** `j = (i + 2) % hislen` in
  del_history_idx; the del spec checks the count, not the order of remaining entries. Spec must
  be strengthened to "the other entries keep their order".
- No unbounded proof (Frama-C WP) for `hislen` up to INT_MAX; no differential test; no
  independent review; no `--unsigned-char` run (these functions read no `char` values).

## Functions still unverified in cmdhist.c (21 of 25)

get_hislen, get_histentry, set_histentry, get_hisidx, get_hisnum, get_history_arg, init_history,
hist_free_entry, clear_hist_entry, in_history, get_histtype, add_to_history, clr_history,
del_history_entry, f_histadd, f_histdel, f_histget, f_histnr, ex_history, hist_iter,
hist_get_array. The four above are bounded-checked only, so none is counted as verified.
