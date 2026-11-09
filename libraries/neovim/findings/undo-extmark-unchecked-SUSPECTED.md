# SUSPECTED (not reproduced): undo-file extmark records reach extmark code unchecked

Status: code reading only, 2026-11-09 08:45 UTC. Not reproduced, no proof. Do not report upstream
until reproduced.

- Path: `u_read_undo` -> `unserialize_uhp` -> `unserialize_extmark` (src/nvim/undo.c) copies
  `sizeof(ExtmarkSplice)` / `sizeof(ExtmarkMove)` raw bytes from the file into the struct
  (`*(ExtmarkSplice *)buf`), with no check on any field. Proved in undo/cbmc/run_ext.sh: the
  object holds exactly the file's bytes.
- Use: `u` / `CTRL-R` -> `u_undoredo` -> `extmark_apply_undo` (src/nvim/extmark.c:529) ->
  `extmark_splice_impl` / `extmark_move_region` with those rows, columns and byte counts.
- What looks unsafe in `extmark_splice_impl` (extmark.c:647) with attacker-chosen ints:
  - `int end_row = start_row + old_row;` and `start_row + old_row` / `start_row + new_row`
    in the `MIN(...)` calls: signed int overflow (UB) for e.g. start_row = INT_MAX, old_row = 1.
  - `buf_signcols_count_range(buf, start_row, row2, ...)` (decoration.c:1040) allocates
    `(size_t)(row2 + 1 - row1)` ints: with a very negative start_row this overflows int (UB) or
    asks for gigabytes (xcalloc failure exits Neovim). Only when 'signcolumn' is "auto" and the
    buffer has sign marks.
  - `marktree_splice` and `buf_updates_send_splice` (sent to nvim_buf_attach / Lua listeners)
    get negative or huge rows; not read yet.
- Also: the record is host-endian raw memory, so an undo file written on one architecture is
  misread on another.
- To confirm: build Neovim with ASan+UBSan, write an undo file (`:wundo`) after a change with an
  extmark present, patch one splice record's start_row to 0x7fffffff, `:rundo`, press `u`.
- Possible fix direction: validate rows/cols/bytes in `unserialize_extmark` (non-negative, and
  rows within the buffer's line count when applied), or reject extmark records from undo files.
