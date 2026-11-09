---
entry: neovim/src/nvim/mark.c (8 helper functions)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
toolchain: Frama-C 33.0 WP (Typed+Cast, RTE, smoke tests), Z3 + CVC5
strength: candidate   # not reviewed yet
platform: x86_64
---

# Claim card: Neovim mark.c helpers (8 of 56 functions)

| Function | Property |
|---|---|
| `free_fmark(fm)` | frees exactly fm.additional_data (once) |
| `free_xfmark(fm)` | frees fm.fname, then fm.fmark.additional_data |
| `clear_fmark(fm, ts)` | frees the old additional_data, then *fm is INIT_FMARK with timestamp ts |
| `free_jumplist(wp)` | frees each entry's fname and additional_data in list order, then the list is empty |
| `mark_view_make(wp, pos)` | view with topline_offset = pos.lnum - w_topline and the window's skipcol, for line numbers in 0..MAXLNUM |
| `mark_check_line_bounds(buf, fm, err)` | false (and *err = e_markinval) iff buf is given and the mark is past the last line; otherwise *err unchanged |
| `next_buffer_mark(buf, name)` | the documented order NUL -> '"' -> '^' -> '.' -> 'a' .. 'z' -> NULL, returning the matching mark of buf |
| `mark_jumplist_iter(iter, win, fm)` | starting at entry 0 (iter NULL) or at iter: copies that entry to *fm and returns the next entry, NULL after the last; an empty list gives INIT_XFMARK and NULL |

xfree is modeled by a ghost log (stubs/vp_mark.h): each call appends the freed pointer, so the contracts say
exactly what is freed and in which order. Preconditions: the documented ones (mark name set, iterator from a previous call) plus 0 <= w_jumplistlen <= JUMPLISTSIZE.
buf_T and win_T are cut down to the fields these functions use (field lines checked against buffer_defs.h);
WP's typed model does not depend on layout. Not yet reviewed by an independent agent.

Reproduce: `bash mark/wp/run_wp.sh <neovim tree> 60`
In progress, not proved: mark_global_iter (25/43 goals; casts from const void *), clrallmarks (91/99 goals; predicate
over fmark_T times out, conjuncts written out prove, see clear_fmark).
