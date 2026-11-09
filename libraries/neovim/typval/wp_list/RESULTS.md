# typval.c list functions: Frama-C WP results

Pinned upstream: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. Frama-C 33.0, Z3 + CVC5,
`-wp-rte -warn-signed-overflow -warn-signed-downcast`, model Typed+Cast, x86_64. No admits,
axioms, assumes or unproved goals. (`axiomatic VpListModel` only *declares* the logic
function `vp_nth`; it contains no axiom.)

Run (Frama-C from `~/.vpipe/bin`, built by `bash /mnt/project-files/pipeline/bootstrap.sh framac`):

    PATH=$HOME/.vpipe/bin:$PATH bash run_wp.sh <neovim checkout at 7b87ce8> 120
    PATH=$HOME/.vpipe/bin:$PATH python3 -I mutants.py <neovim checkout> 20

| Function | File | Goals | Status |
|---|---|---|---|
| tv_list_len | typval.h | 6 / 6 | proved |
| tv_list_uidx | typval.h | 19 / 19 | proved |
| tv_list_find | typval.c | 80 / 80 | proved (precondition P1) |
| tv_list_idx_of_item | typval.c | 23 / 23 | proved |
| tv_list_find_index (static) | typval.c | 28 / 28 | proved (P1) |
| tv_list_check_range_index_one | typval.c | 21 / 21 | proved (P1) |
| tv_list_check_range_index_two | typval.c | 38 / 38 | proved (P1) |
| tv_list_reverse | typval.c | 54 / 54 | proved (precondition P2) |
| tv_list_find_nr, tv_list_find_str | typval.c | - | unproved: not trivial, they call tv_get_number_chk / tv_get_string (not modelled here) |

Final full-run output: `full_run.txt`. Planted bugs: `mutants_result.txt` (14 code mutants, each must fail).

## Model

`vp_nth(l, i)` is the item sequence of `l` (uninterpreted, so each proof holds for every
sequence). `wf_list(l)`: `l` valid, `0 <= lv_len`, item i valid and separated from `l` and
from every other item, `li_next`/`li_prev` link neighbours (NULL at the ends), `lv_first` /
`lv_last` are the ends (both NULL when empty), and a non-NULL `lv_idx_item` is item `lv_idx`.
This is the list invariant every list function relies on; it is a precondition, listed here.
`semsg` is a stub that counts messages (`vp_msgs`), so specs say exactly when an error is shown.
`assert(e)` becomes a call whose precondition is `e` (proved). `li_tv` is elided from
`listitem_S` (never read by these functions); `TV_LIST_ITER_CONST` is expanded from the pinned
typval.h macro text by build.py.

## Specs (from the doc comments)

- tv_list_find(l, n): NULL for NULL l or out-of-range n (negative counts from the end);
  otherwise item number uidx(n), and the cache becomes (uidx(n), that item); wf_list kept.
- tv_list_idx_of_item(l, item): the index of `item` in `l`, or -1 (also for NULL l).
- tv_list_find_index(l, idx): as find; a negative out-of-range index is clamped to 0 (*idx = 0).
- tv_list_check_range_index_one: as find_index, plus one error message when it returns NULL and !quiet.
- tv_list_check_range_index_two: negative *n2 out of range -> FAIL (+message); else *n2, *n1 are
  normalised and the result is OK iff *n2 >= *n1 (+message on FAIL when !quiet). Precondition from
  the doc: when *n1 < 0, li1 is the item for n1.
- tv_list_reverse: for 2+ items, first/last swap, every item's next/prev swap, and
  lv_idx = len - lv_idx - 1 (so a cached item keeps pointing at its new index); 0 or 1 items: no change.

## Preconditions that are not plain list well-formedness (candidate findings)

- **P1 (tv_list_find)**: `lv_idx_item != NULL ==> lv_idx + lv_len <= INT_MAX`. The code computes
  `(l->lv_idx + l->lv_len) / 2` in `int`; with a cached index this overflows (UB) once the list has
  more than about 1.07e9 items (lv_idx near lv_len). Needs ~34 GB of list items; not reproduced.
  A fix would be `l->lv_idx + (l->lv_len - l->lv_idx) / 2`. Not proved as a fix here.
- **P2 (tv_list_reverse)**: `INT_MIN + 1 <= lv_len - lv_idx <= INT_MAX`. Always true while lv_idx is a
  valid cached index; but lv_idx is left stale when lv_idx_item is cleared, and
  tv_list_insert (typval.c:432, out of this scope) does `l->lv_idx++` on every insert at the
  front even when the cache is empty. So lv_idx can drift (insert-at-front / remove loops), and
  after 2^31 such inserts `lv_idx++` itself overflows (signed overflow UB); a later reverse can
  then overflow too. Harmless in value (a stale lv_idx is never read without lv_idx_item) but UB.
  Not reproduced (needs ~2^31 Vimscript iterations). Worth a look by whoever proves tv_list_insert.
