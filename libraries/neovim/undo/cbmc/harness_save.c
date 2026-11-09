// u_update_save_nr: increments the write counter, makes it current, and stores it in the header
// that "u" would undo next (curhead's next when a header is current, else the newest), if any.
// Nothing else changes. Precondition: the counter is below INT_MAX (one increment per file write).
#include SAVE_C
int nondet_int(void); _Bool nondet_bool(void);
void h_update_save_nr(void) {
  u_header_T cur, nxt, newest; buf_T b;
  cur.uh_save_nr = nondet_int(); nxt.uh_save_nr = nondet_int(); newest.uh_save_nr = nondet_int();
  cur.uh_next.ptr = nondet_bool() ? &nxt : NULL;
  b.b_u_curhead = nondet_bool() ? &cur : NULL; b.b_u_newhead = nondet_bool() ? &newest : NULL;
  b.b_u_save_nr_last = nondet_int(); b.b_u_save_nr_cur = nondet_int();
  if (b.b_u_save_nr_last == INT_MAX) return;
  int n0 = b.b_u_save_nr_last, c0 = cur.uh_save_nr, x0 = nxt.uh_save_nr, w0 = newest.uh_save_nr;
  u_header_T *target = b.b_u_curhead != NULL ? cur.uh_next.ptr : b.b_u_newhead;
  u_update_save_nr(&b);
  assert(b.b_u_save_nr_last == n0 + 1 && b.b_u_save_nr_cur == n0 + 1);
  assert(cur.uh_save_nr == c0);
  assert(nxt.uh_save_nr == (target == &nxt ? n0 + 1 : x0));
  assert(newest.uh_save_nr == (target == &newest ? n0 + 1 : w0));
}
