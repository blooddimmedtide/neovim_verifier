#include "prelude.h"
#include GRID_C
#include "spec.h"
unsigned nondet_unsigned(void); int nondet_int(void); char nondet_char(void);
// Glyph cache model: n_keys exact-size bytes; the entry at idx is NUL terminated within
// MAX_SCHAR_SIZE bytes (assert(idx < n_keys) in the code + the cache's size invariant).
static void setup_cache(schar_T sc) {
  uint32_t n = nondet_unsigned();
  __CPROVER_assume(n >= 1 && n <= 40);
  glyph_cache.h.n_keys = n;
  glyph_cache.keys = malloc(n);
  if (ref_high(sc)) {
    uint32_t idx = ref_idx(sc);
    __CPROVER_assume(idx < n);
    uint32_t j = nondet_unsigned();
    __CPROVER_assume(j < MAX_SCHAR_SIZE && idx + j < n && glyph_cache.keys[idx + j] == 0);
  }
}
static schar_T any_sc(void) {
  schar_T sc = nondet_unsigned();
  // Non-high cells hold NUL-padded text: no NUL followed by a non-NUL byte.
  unsigned char b[4]; bytes_of(sc, b);
  if (b[0] != 0xFF) for (int i = 0; i < 3; i++) __CPROVER_assume(b[i] != 0 || b[i + 1] == 0);
  return sc;
}
void h_schar_high(void) { schar_T sc = nondet_unsigned(); assert(schar_high(sc) == ref_high(sc)); }
void h_schar_get_ascii(void) {
  schar_T sc = nondet_unsigned(); unsigned char b[4]; bytes_of(sc, b);
  char want = (b[0] < 0x80 && b[1] == 0 && b[2] == 0 && b[3] == 0) ? (char)b[0] : NUL;
  assert(schar_get_ascii(sc) == want);
}
void h_schar_len(void) {
  schar_T sc = any_sc(); setup_cache(sc); size_t n; char tmp[5];
  ref_text(sc, &n, tmp); assert(schar_len(sc) == n);
}
void h_schar_get_adv(void) {
  schar_T sc = any_sc(); setup_cache(sc); size_t n; char tmp[5];
  const char *t = ref_text(sc, &n, tmp);
  char *buf = malloc(MAX_SCHAR_SIZE); char *p = buf;
  size_t r = schar_get_adv(&p, sc);
  assert(r == n && p == buf + n);
  for (size_t i = 0; i < n; i++) assert(buf[i] == t[i]);
}
void h_schar_get(void) {
  schar_T sc = any_sc(); setup_cache(sc); size_t n; char tmp[5];
  const char *t = ref_text(sc, &n, tmp);
  char *buf = malloc(MAX_SCHAR_SIZE);
  size_t r = schar_get(buf, sc);
  assert(r == n && n < MAX_SCHAR_SIZE && buf[n] == NUL);
  for (size_t i = 0; i < n; i++) assert(buf[i] == t[i]);
}
void h_schar_get_first_byte(void) {
  schar_T sc = any_sc(); setup_cache(sc); size_t n; char tmp[5];
  const char *t = ref_text(sc, &n, tmp);
  assert(schar_get_first_byte(sc) == t[0]);
}
void h_schar_in_arabic_block(void) {
  schar_T sc = any_sc(); setup_cache(sc); size_t n; char tmp[5];
  unsigned char f = (unsigned char)ref_text(sc, &n, tmp)[0];
  assert(schar_in_arabic_block(sc) == (f == 0xD8 || f == 0xD9));  // U+0600..U+07FF lead bytes
}
void h_schar_from_char(void) {
  int c = nondet_int(); __CPROVER_assume(c >= 0);   // documented: "a unicode character"
  unsigned char want[4] = { 0 };
  ref_utf8(c < 0x200000 ? c : 0xFFFD, want);
  schar_T sc = schar_from_char(c); unsigned char b[4]; bytes_of(sc, b);
  for (int i = 0; i < 4; i++) assert(b[i] == want[i]);
}
void h_grid_adjust(void) {
  GridView v; ScreenGrid g; v.target = &g; v.row_offset = nondet_int(); v.col_offset = nondet_int();
  int r = nondet_int(), c = nondet_int(); int r0 = r, c0 = c;
#ifndef NO_OFFSET_PRE
  // Caller precondition (NOT documented): screen positions fit in int.
  __CPROVER_assume((long)r + v.row_offset >= INT_MIN && (long)r + v.row_offset <= INT_MAX);
  __CPROVER_assume((long)c + v.col_offset >= INT_MIN && (long)c + v.col_offset <= INT_MAX);
#endif
  ScreenGrid *res = grid_adjust(&v, &r, &c);
  assert(res == &g && (long)r == (long)r0 + v.row_offset && (long)c == (long)c0 + v.col_offset);
}
// Grid model (grid_defs.h comment): rows*cols cells in chars/attrs, line_offset[r] is where row r
// starts, and the whole row fits: line_offset[r] + cols <= rows*cols (grid_alloc's layout; rows are
// rotated by scrolling, never shortened). Only the accessed row's entry is constrained.
static void setup_grid(ScreenGrid *g, int row) {
  g->rows = nondet_int(); g->cols = nondet_int();
  __CPROVER_assume(g->rows >= 1 && g->cols >= 1 && g->rows <= 65535 && g->cols <= 65535);
  size_t n = (size_t)g->rows * (size_t)g->cols;
  g->chars = malloc(n * sizeof(schar_T)); g->attrs = malloc(n * sizeof(sattr_T));
  g->vcols = malloc(n * sizeof(colnr_T)); g->line_offset = malloc((size_t)g->rows * sizeof(size_t));
  if (row >= 0 && row < g->rows) __CPROVER_assume(g->line_offset[row] <= n - (size_t)g->cols);
}
void h_grid_invalid_row(void) {
  ScreenGrid g; int row = nondet_int(); setup_grid(&g, row);
  __CPROVER_assume(row >= 0 && row < g.rows);   // static; every caller passes a grid row
  assert(grid_invalid_row(&g, row) == (g.attrs[g.line_offset[row]] < 0));
}
void h_grid_getchar(void) {
  ScreenGrid g; int row = nondet_int(), col = nondet_int(); setup_grid(&g, row);
  if (nondet_int()) g.chars = NULL;
#ifndef NO_NEG_PRE
  // Caller precondition (NOT documented, checked by all 3 callers in eval/funcs.c): row, col >= 0.
  __CPROVER_assume(row >= 0 && col >= 0);
#endif
  int attr = nondet_int(), a0 = attr; bool want_attr = nondet_int() != 0;
  schar_T r = grid_getchar(&g, row, col, want_attr ? &attr : NULL);
  if (g.chars == NULL || row >= g.rows || col >= g.cols) { assert(r == 0 && attr == a0); }
  else {
    size_t off = g.line_offset[row] + (size_t)col;
    assert(r == g.chars[off]);
    assert(attr == (want_attr ? g.attrs[off] : a0));
  }
}
// State left by screengrid_line_start (its assignments and asserts): a grid with a valid row,
// 0 <= coloff, maxcol = MIN(cols, cols - coloff) <= linebuf_size, linebuf_* of linebuf_size cells.
static void setup_line(ScreenGrid *g) {
  int row = nondet_int(); setup_grid(g, row); __CPROVER_assume(row >= 0 && row < g->rows);
  int coloff = nondet_int(); __CPROVER_assume(coloff >= 0 && coloff < g->cols);
  linebuf_size = nondet_unsigned(); __CPROVER_assume(linebuf_size <= 65535);
  grid_line_grid = g; grid_line_row = row; grid_line_coloff = coloff;
  grid_line_maxcol = MIN(g->cols, g->cols - coloff);
  __CPROVER_assume((size_t)grid_line_maxcol <= linebuf_size);
  linebuf_char = malloc(linebuf_size * sizeof(schar_T)); linebuf_attr = malloc(linebuf_size * sizeof(sattr_T));
  linebuf_vcol = malloc(linebuf_size * sizeof(colnr_T));
  grid_line_first = nondet_int(); grid_line_last = nondet_int();
}
void h_grid_line_getchar(void) {
  ScreenGrid g; setup_line(&g);
  int col = nondet_int();
  __CPROVER_assume(col >= 0);   // NOT documented; every caller passes a column >= 0
  int attr = nondet_int(), a0 = attr; bool want = nondet_int() != 0;
  schar_T r = grid_line_getchar(col, want ? &attr : NULL);
  if (col >= grid_line_maxcol) { assert(r == ' ' && attr == a0); }   // "space if out of bounds"
  else {
    size_t off = g.line_offset[grid_line_row] + (size_t)(col + grid_line_coloff);
    assert(r == g.chars[off] && attr == (want ? g.attrs[off] : a0));
  }
}
void h_grid_line_put_schar(void) {
  ScreenGrid g; setup_line(&g);
  int col = nondet_int(); __CPROVER_assume(col >= 0);   // NOT documented, as above
  schar_T sc = nondet_unsigned(); int attr = nondet_int();
  int f0 = grid_line_first, l0 = grid_line_last;
  size_t k = nondet_unsigned(); __CPROVER_assume(k < linebuf_size && k != (size_t)col);
  schar_T ck = linebuf_char[k]; sattr_T ak = linebuf_attr[k]; colnr_T vk = linebuf_vcol[k];
  grid_line_put_schar(col, sc, attr);
  if (col >= grid_line_maxcol) { assert(grid_line_first == f0 && grid_line_last == l0); }
  else {
    assert(linebuf_char[col] == sc && linebuf_attr[col] == attr && linebuf_vcol[col] == -1);
    assert(grid_line_first == MIN(f0, col) && grid_line_last == MAX(l0, col + 1));
  }
  assert(linebuf_char[k] == ck && linebuf_attr[k] == ak && linebuf_vcol[k] == vk);  // nothing else written
}
void h_grid_line_cursor_goto(void) {
  ScreenGrid g; setup_line(&g); g.handle = nondet_int(); int col = nondet_int();
  grid_line_cursor_goto(col);
  assert(rec_calls == 1 && rec_grid == g.handle && rec_row == grid_line_row && rec_col == col);
}
