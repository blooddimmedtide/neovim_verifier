# src/nvim/grid.c (upstream 7b87ce8): 48 functions

Proved (candidate, CBMC, see CLAIM.md): schar_high, schar_get_ascii, schar_len, schar_get_adv,
schar_get, schar_get_first_byte, schar_in_arabic_block, schar_from_char, grid_adjust (under an
undocumented no-overflow precondition).

Still unverified (39): schar_from_str, schar_from_buf (needs the glyph set_put_idx proof from map.c),
schar_cache_clear_if_full, schar_cache_clear, schar_cells, schar_get_first_codepoint,
schar_get_first_two_codepoints, line_do_arabic_shape, grid_clear_line, grid_invalidate,
grid_invalid_row, grid_getchar, grid_line_start, screengrid_line_start, grid_line_getchar,
grid_line_put_schar, grid_line_puts, grid_line_fill, grid_line_clear_end, grid_line_cursor_goto,
grid_line_mirror, linebuf_mirror, grid_line_flush, grid_line_flush_if_valid_row, grid_clear,
grid_char_needs_redraw, grid_put_linebuf, grid_alloc, grid_free, grid_free_all_mem, win_grid_alloc,
grid_assign_handle, grid_ins_lines, grid_del_lines, grid_draw_bordertext, get_bordertext_col,
grid_draw_border, linecopy, get_win_by_grid_handle.

Next: the line/cell bound functions (grid_clear_line, grid_invalid_row, linecopy, grid_getchar,
grid_line_* ) with Frama-C WP over a ScreenGrid model (rows*cols cells, line_offset table);
use the ghost "avoid" style of typval/wp_blob for allocation, not the garray xrealloc stub.
Also open: differential test, independent review.
