# src/nvim/indent.c: tabstop helpers (work in progress)

Pinned upstream: neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. Tool: CBMC 6.4.1
(`cbmc/run_cbmc.sh`), verbatim extraction with sha256 pins (`cbmc/build.py`).

## State at the 2026-11-09 09:00 UTC stop

- **Proved** (CBMC, signed and unsigned char, x86_64): `tabstop_count`, `tabstop_first`.
- **Harness written, run not finished** (CBMC still solving after 15+ minutes, killed at the
  deadline; most likely the 32-bit `%` on unbounded columns): `tabstop_padding`,
  `tabstop_at`, `tabstop_start`, `tabstop_fromto`. These are NOT proved. Next step: split the
  column range (col < S_n vs. col >= S_n) or prove them in Frama-C WP instead.
- No bugs found. `tabstop_at(left=true)` left of the first stop returns `ts` with no list but
  `col` with one; the function's comment only promises "at least that distance", so the
  harness checks `>= col` there (a spec choice, listed for review).

## Properties the harness checks

Each function is checked against `cbmc/harness.c`'s reference, which is written from
`:help 'vartabstop'`: tab stops at the running sums of the list, then every last width.
Checks on: bounds, pointers, signed overflow, division by zero, unwinding assertions;
signed and unsigned char; x86_64.

| Function | Property |
|---|---|
| tabstop_padding | columns to the next stop strictly after `col` |
| tabstop_at | width of the interval holding `col`; with `left`, the one before it, or `col` in the first interval |
| tabstop_start | the last stop at or before `col` (0 if none) |
| tabstop_fromto | tabs = stops in (start, end]; spaces = end minus the last such stop (or start) |
| tabstop_count, tabstop_first | `ts[0]` / `ts[1]`; 0 / 8 for NULL |

## Limits (stated plainly)

- **Bounded proof**: lists of 0..4 entries (MAXN). Columns are any int >= 0 and every width
  is any value in 1..TABSTOP_MAX, so only the list length is bounded. Longer lists are not
  proved; a WP proof with loop invariants is needed for that.
- Preconditions (what tabstop_set and the option checks guarantee, not asserted by the
  functions): list entries in 1..9999 (tabstop_set rejects others); 'tabstop' in 1..9999;
  `col >= 0`; `start_col <= end_col` for tabstop_fromto; tabstop_first needs `ts[0] >= 1`
  (it reads `ts[1]` otherwise; tabstop_set never makes an empty list, it uses NULL).
- No differential test, no mutant review yet.

## Still unverified in indent.c (33 of 39)

tabstop_set, tabstop_copy, get_sw_value, get_sw_value_pos, get_sw_value_indent,
get_sw_value_col, get_sts_value, get_indent, get_indent_lnum, get_indent_buf,
indent_size_no_ts, indent_size_ts, set_indent, get_number_indent, briopt_check,
get_breakindent_win, inindent, op_reindent, preprocs_left, may_do_si, ins_try_si,
change_indent, copy_indent, emsg_text_too_long, ex_retab, get_expr_indent,
get_lisp_indent, lisp_match, fixthisline, use_indentexpr_for_lisp, fix_indent,
f_indent, f_lispindent.
