// u_clearline: frees the saved "U" line and sets the pointer to NULL and its line number to 0;
// with no saved line it changes nothing. No leak (--memory-leak-check).
// u_update_named_mark(buf, idx), 0 <= idx < NMARKS: zeroes lnum of mark idx in the current
// header, else the newest, if any; nothing else changes.
#include MISC_C
int nondet_int(void); _Bool nondet_bool(void);
void h_clearline(void) {
  buf_T b; b.b_u_line_ptr = nondet_bool() ? malloc(1) : NULL; b.b_u_line_lnum = nondet_int();
  char *p0 = b.b_u_line_ptr; linenr_T l0 = b.b_u_line_lnum;
  u_clearline(&b);
  assert(b.b_u_line_ptr == NULL);
  assert(b.b_u_line_lnum == (p0 == NULL ? l0 : 0));
}
void h_update_named_mark(void) {
  static u_header_T cur, newest; buf_T b;
  b.b_u_curhead = nondet_bool() ? &cur : NULL; b.b_u_newhead = nondet_bool() ? &newest : NULL;
  int idx = nondet_int(); if (idx < 0 || idx >= NMARKS) return;   // callers pass a mark index
  int j = nondet_int(); if (j < 0 || j >= NMARKS) return;          // any mark, to check the rest
  cur.uh_namedm[j].mark.lnum = nondet_int(); newest.uh_namedm[j].mark.lnum = nondet_int();
  cur.uh_namedm[j].mark.col = nondet_int();
  linenr_T c0 = cur.uh_namedm[j].mark.lnum, n0 = newest.uh_namedm[j].mark.lnum;
  colnr_T col0 = cur.uh_namedm[j].mark.col;
  u_header_T *t = b.b_u_curhead != NULL ? &cur : b.b_u_newhead;
  u_update_named_mark(&b, idx);
  assert(cur.uh_namedm[j].mark.lnum == (t == &cur && j == idx ? 0 : c0));
  assert(newest.uh_namedm[j].mark.lnum == (t == &newest && j == idx ? 0 : n0));
  assert(cur.uh_namedm[j].mark.col == col0);
}
