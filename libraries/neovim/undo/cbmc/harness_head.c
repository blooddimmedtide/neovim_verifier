// u_get_headentry: the newest header's first entry, or NULL with one internal error when there
// is no newest header or it has no entry.
// u_getbot: when the header list is valid and a getbot entry is pending, sets its ue_bot to
// ue_top + ue_size + 1 + (line count now - ue_lcount), or to ue_top + 1 with one internal error
// when that is outside 1 .. line count; clears the pending entry and sets b_u_synced. With no
// valid list it only reports the error.
#include HEAD_C
int nondet_int(void); _Bool nondet_bool(void);
typedef __int128 i128;

void h_get_headentry(void) {
  u_entry_T e; u_header_T h; buf_T b;
  h.uh_entry = nondet_bool() ? &e : NULL; b.b_u_newhead = nondet_bool() ? &h : NULL;
  iemsg_calls = 0;
  u_entry_T *r = u_get_headentry(&b);
  bool ok = b.b_u_newhead != NULL && h.uh_entry != NULL;
  assert(r == (ok ? &e : NULL));
  assert(iemsg_calls == (ok ? 0 : 1));
}

// Preconditions, from how undo.c sets these fields (u_savecommon): line numbers and counts are
// >= 0, ue_top + ue_size + 1 (the old ue_bot) is at most the line count at save time plus one, and
// both line counts are below MAXLNUM (0x7fffffff). With a line count of exactly MAXLNUM the sums
// overflow int; such a buffer (2^31 - 1 lines) is outside this claim, see CLAIM.md.
void h_getbot(void) {
  u_entry_T e, g; u_header_T h; buf_T b;
  g.ue_top = nondet_int(); g.ue_size = nondet_int(); g.ue_lcount = nondet_int(); g.ue_bot = nondet_int();
  b.b_ml.ml_line_count = nondet_int(); b.b_u_synced = nondet_bool();
  if (g.ue_top < 0 || g.ue_size < 0 || g.ue_lcount < 0 || b.b_ml.ml_line_count < 0) return;
  if ((i128)g.ue_top + g.ue_size + 1 > (i128)g.ue_lcount + 1) return;
  if (g.ue_lcount >= 0x7fffffff || b.b_ml.ml_line_count >= 0x7fffffff) return;
  h.uh_entry = nondet_bool() ? &e : NULL; h.uh_getbot_entry = nondet_bool() ? &g : NULL;
  b.b_u_newhead = nondet_bool() ? &h : NULL;
  bool valid = b.b_u_newhead != NULL && h.uh_entry != NULL;
  bool pending = valid && h.uh_getbot_entry != NULL;
  linenr_T top = g.ue_top, bot0 = g.ue_bot; bool synced0 = b.b_u_synced;
  i128 want = (i128)g.ue_top + g.ue_size + 1 + ((i128)b.b_ml.ml_line_count - g.ue_lcount);
  bool bad = want < 1 || want > b.b_ml.ml_line_count;
  iemsg_calls = 0;
  u_getbot(&b);
  if (!valid) {
    assert(iemsg_calls == 1 && b.b_u_synced == synced0 && g.ue_bot == bot0);
  } else {
    assert(b.b_u_synced);
    assert(h.uh_getbot_entry == NULL);
    if (pending) {
      assert(g.ue_bot == (bad ? top + 1 : (linenr_T)want));
      assert(iemsg_calls == (bad ? 1 : 0));
    } else {
      assert(iemsg_calls == 0 && g.ue_bot == bot0);
    }
  }
}
