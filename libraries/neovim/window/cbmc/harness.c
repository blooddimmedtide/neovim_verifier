// CBMC proofs for window-size arithmetic in src/nvim/window.c, every input.
// References are written from the documented meaning (see CLAIM.md), not the code.
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include WINDOW_C

int nondet_int(void);
char nondet_char(void);
int64_t nondet_i64(void);
unsigned nondet_unsigned(void);

// 'scroll' default: half the window height, at least 1 (:help 'scroll').
void h_default_scroll(void) {
  win_T w; win_T *wp = &w;
  wp->w_view_height = nondet_int();
  OptInt r = win_default_scroll(wp);
  OptInt half = wp->w_view_height / 2;  // C division truncates toward zero
  __CPROVER_assert(r >= 1, "at least 1");
  __CPROVER_assert(half >= 1 ? r == half : r == 1, "half the height, else 1");
}

// set_fraction: for a window of h > 1 rows, w_fraction = (wrow + 1/2) / h scaled by 16384,
// rounded down; with h <= 1 unchanged. Precondition (window invariant): 0 <= wrow < h.
void h_set_fraction(void) {
  win_T w; win_T *wp = &w;
  wp->w_view_height = nondet_int();
  wp->w_wrow = nondet_int();
  int old = nondet_int();
  wp->w_fraction = old;
  int h = wp->w_view_height, row = wp->w_wrow;
  __CPROVER_assume(h <= 1 || (0 <= row && row < h));
  // the screen grid limits rows; Rows is an int and the grid is Rows*Columns cells
  __CPROVER_assume(h <= 131071);
  set_fraction(wp);
  if (h <= 1) { __CPROVER_assert(wp->w_fraction == old, "unchanged"); return; }
  int64_t num = (int64_t)(2 * row + 1) * 16384;  // (row + 1/2) * 16384, doubled
  int64_t f = wp->w_fraction;
  __CPROVER_assert(f * 2 * h <= num && num < (f + 1) * 2 * h, "floor((row+1/2)*16384/h)");
  __CPROVER_assert(0 <= f && f < 16384, "inside [0, FRACTION_MULT)");
}

#define NCH 4
// Build a frame with up to NCH children, every field nondeterministic.
static frame_T *mk(int *n_out) {
  static frame_T topf; frame_T *top = &topf;
  top->fr_layout = nondet_char(); top->fr_width = nondet_int(); top->fr_height = nondet_int();
  top->fr_next = NULL;
  unsigned n = nondet_unsigned(); __CPROVER_assume(n <= NCH);
  static frame_T kids[NCH];
  for (unsigned i = 0; i < n; i++) {
    kids[i].fr_layout = nondet_char(); kids[i].fr_width = nondet_int(); kids[i].fr_height = nondet_int();
    kids[i].fr_child = NULL; kids[i].fr_next = i + 1 < n ? &kids[i + 1] : NULL;
  }
  top->fr_child = n ? kids : NULL;
  *n_out = (int)n;
  return top;
}

// frame_check_height: true iff the frame has that height and, for a row layout,
// every child has it too (children of a row share the row's height).
void h_check_height(void) {
  int n; frame_T *t = mk(&n); int v = nondet_int();
  bool want = t->fr_height == v;
  if (t->fr_layout == FR_ROW) for (int i = 0; i < n; i++) want = want && t->fr_child[i].fr_height == v;
  __CPROVER_assert(frame_check_height(t, v) == want, "frame_check_height");
}

// frame_check_width: the same for widths and column layouts.
void h_check_width(void) {
  int n; frame_T *t = mk(&n); int v = nondet_int();
  bool want = t->fr_width == v;
  if (t->fr_layout == FR_COL) for (int i = 0; i < n; i++) want = want && t->fr_child[i].fr_width == v;
  __CPROVER_assert(frame_check_width(t, v) == want, "frame_check_width");
}

// global_stl_height: 'laststatus' 3 means one global statusline of height 1 (:help 'ls').
void h_global_stl(void) {
  p_ls = nondet_i64();
  __CPROVER_assert(global_stl_height() == (p_ls == 3 ? 1 : 0), "global_stl_height");
}
