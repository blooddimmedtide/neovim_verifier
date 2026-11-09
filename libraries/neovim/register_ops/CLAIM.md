---
entry: neovim/src/nvim/register.c + src/nvim/ops.c (register and operator helpers; partial, 18 of 101 functions)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-dvm5iw, commit 09421b0: get_vts_sum)
toolchain: Frama-C 33 WP + Z3 + CVC5 (Nix, tools/install.sh), CBMC 6.4.1
strength: candidate   # no independent review yet; owner sign-off needed
platform: x86_64, char signed and unsigned (WP: machdep_x86_64_uchar.yaml differs only in char_is_unsigned; CBMC: --unsigned-char)
---

# Claim card: register.c / ops.c helpers

Every piece is the exact upstream text, sha256 pinned (`wp/pins.txt`, `wp/pins_fixed.txt`);
`wp/build.py` refuses to build if a piece changed and checks that removing the ACSL gives back
the verbatim text. The reference (`wp/contracts.py`) is written from the documentation
(ops.h operator comments, :help operator / registers / 'vartabstop'), not from `opchars[]`.

## Proved, Frama-C WP (every goal, smoke tests on, no admit/axiom)

| Function | Property |
|---|---|
| `get_op_type(c1, c2)` | for a valid operator name: `r` -> OP_REPLACE, `~` -> OP_TILDE, `g^A`/`g^X` -> OP_NR_ADD/SUB, `zy` -> OP_YANK, otherwise the first operator whose documented command is (c1, c2). The internal_error branch is proved unreachable. |
| `op_on_lines(op)` | 1 if op is linewise, else 0 |
| `op_is_change(op)` | 2 if op changes text, else 0 |
| `op_redoable(op, y)` | y for yank, otherwise whether op changes text |
| `get_op_char`, `get_extra_op_char` | first / second command character of op |
| `get_vts(a, i)` | i-th 'vartabstop' width, 0 for i < 1, the last width past the end |
| `get_vts_sum(a, n)` | sum of the first n tabstop widths. Upstream: only when the result fits in int (see Finding). Fixed fork: for every n. |
| `op_self_select(cap)` | true exactly for the commands gn, gN, gv |
| `get_y_register(r)` | `&y_regs[r]` |
| `get_y_previous()` | `y_previous` |
| `op_reg_amount()` | number of non-empty registers among the 37 saved ones |
| `op_reg_get(name)` | NULL for a name with no register, else that register (A-Z same as a-z) |
| `op_reg_set_previous(name)` | false and nothing changed for an unknown name, else true and `y_previous` set to that register |

Also proved (header helpers used above): `ascii_isdigit`, `op_reg_index`, `get_register_name`, `reg_empty`.

## Proved, CBMC (bounded state fully unwound, unwinding assertions)

| Function | Property |
|---|---|
| `get_unname_register()` | -1 when `y_previous` is NULL, else its index |
| `op_reg_iter`, `op_global_reg_iter` | from NULL or any register pointer: name, contents and is_unnamed of the first non-empty register at or after it, and a pointer to the next non-empty one (NULL at the end); name NUL and NULL when none. Register lines: each register has 0-3 lines (reg_empty only looks at y_size 0, 1, more) |
| `valid_yank_reg(c, writing)` | true exactly for 0-9, a-z, A-Z, `"`, `-`, `_`, `*`, `+`, and (only when not writing) `/ # . % : =`; every int c. vim_strchr and utf_char2bytes are run verbatim; strstr is a plain C-standard model (CBMC has none) |

## Relied on (preconditions)
- `op` / `optype` in 0..30 (callers pass OP_* values); `get_op_type` only gets valid names (documented: "Must only be called with a valid operator name!").
- `get_y_register(r)`: 0 <= r < 39. Not documented; every caller passes op_reg_index results or constants.
- `y_previous` is NULL or points into `y_regs` (the file only ever assigns those).
- 'vartabstop' arrays: 1 <= a[0] < 100000, widths 1..9999 (TABSTOP_MAX, enforced by tabstop_set; shift_line checks a[0] != 0).
- Register arrays readable as reg_empty reads them.

## Finding
`findings/vts-sum-overflow.md`: signed int overflow in `get_vts_sum` on `V999999999>` with sw=0 and 'vartabstop'. Fixed in the fork (int64_t), fix proved.

## Not done
83 functions are unverified; list in PLAN.md. Planted bugs chosen by the proving session: 23/23 caught (`run_mutants.py`, WP functions) and 9/9 for the CBMC harnesses (`cbmc/run_mutants.py`). No independent review, CI not run.
