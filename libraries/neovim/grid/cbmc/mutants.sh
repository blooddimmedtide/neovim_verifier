#!/bin/bash
# Planted bugs: each must make run_cbmc.sh fail. Usage: bash mutants.sh <neovim checkout>
HERE=$(cd "$(dirname "$0")" && pwd); NV=$(cd "$1" && pwd); caught=0; total=0
run() { # name harness sed-expression function
  T=$(mktemp -d); mkdir -p "$T/src/nvim"; cp "$NV/src/nvim/grid.c" "$NV/src/nvim/mbyte.c" "$T/src/nvim/"
  sed -i "$3" "$T/src/nvim/grid.c"
  if cmp -s "$T/src/nvim/grid.c" "$NV/src/nvim/grid.c"; then echo "$1: mutation did not apply"; rm -rf "$T"; return; fi
  total=$((total+1))
  if SKIP_PINS="$4" HARNESSES="$2" bash "$HERE/run_cbmc.sh" "$T" >/dev/null 2>&1; then echo "$1: SURVIVED"
  else echo "$1: caught"; caught=$((caught+1)); fi; rm -rf "$T"
}
run high-mask h_schar_high 's/return ((sc \& 0xFF) == 0xFF);/return ((sc \& 0xFE) == 0xFE);/' schar_high
run ascii-bound h_schar_get_ascii 's/return (sc < 0x80) ? (char)sc : NUL;/return (sc <= 0x80) ? (char)sc : NUL;/' schar_get_ascii
run len-strnlen3 h_schar_len '/^size_t schar_len/,/^}/s/strnlen((char \*)\&sc, 4)/strnlen((char *)\&sc, 3)/' schar_len
run getadv-noadv h_schar_get_adv 's/  \*buf_out += len;/  *buf_out += len - (len > 1);/' schar_get_adv
run get-nonul h_schar_get 's/  \*buf_out = NUL;/  *buf_out = 1;/' schar_get
run firstbyte-off h_schar_get_first_byte 's/glyph_cache.keys\[schar_idx(sc)\] : \*(char \*)\&sc;/glyph_cache.keys[schar_idx(sc) + 1] : *(char *)\&sc;/' schar_get_first_byte
run arabic-mask h_schar_in_arabic_block 's/\& 0xFE) == 0xD8;/\& 0xFC) == 0xD8;/' schar_in_arabic_block
run fromchar-limit h_schar_from_char 's/if (c >= 0x200000) {/if (c > 0x200000) {/' schar_from_char
run fromchar-repl h_schar_from_char 's/    c = 0xFFFD;/    c = 0xFFFE;/' schar_from_char
run adjust-swap h_grid_adjust 's/\*col_off += grid->col_offset;/*col_off += grid->row_offset;/' grid_adjust
run invalid-le h_grid_invalid_row 's/return grid->attrs\[grid->line_offset\[row\]\] < 0;/return grid->attrs[grid->line_offset[row]] <= 0;/' grid_invalid_row
run getchar-ge h_grid_getchar 's/row >= grid->rows || col >= grid->cols) {/row > grid->rows || col >= grid->cols) {/' grid_getchar
run getchar-attr h_grid_getchar 's/    \*attrp = grid->attrs\[off\];/    *attrp = grid->attrs[off - (off > 0)];/' grid_getchar
run lgetchar-le h_grid_line_getchar 's/  if (col < grid_line_maxcol) {/  if (col <= grid_line_maxcol) {/' grid_line_getchar
run lgetchar-nooff h_grid_line_getchar 's/    col += grid_line_coloff;/    col += 0;/' grid_line_getchar
run put-last h_grid_line_put_schar 's/grid_line_last = MAX(grid_line_last, col + 1);/grid_line_last = MAX(grid_line_last, col);/' grid_line_put_schar
run put-novcol h_grid_line_put_schar 's/  linebuf_vcol\[col\] = -1;/  linebuf_vcol[col] = 0;/' grid_line_put_schar
run goto-col h_grid_line_cursor_goto 's/ui_grid_cursor_goto(grid_line_grid->handle, grid_line_row, col);/ui_grid_cursor_goto(grid_line_grid->handle, col, grid_line_row);/' grid_line_cursor_goto
echo "caught $caught/$total"
