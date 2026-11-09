// undo_allowed(buf): false with exactly one message when 'modifiable' is off (E21), else in the
// sandbox (E48), else under textlock or an expression mapping on a non-dummy current buffer (E565),
// checked in that order; otherwise true with no message.
// corruption_error(mesg, name): one E825 message with mesg and name as its two arguments.
#include ALLOW_C
int nondet_int(void); _Bool nondet_bool(void);
void h_undo_allowed(void) {
  buf_T b, c; b.b_p_ma = nondet_int(); c.b_flags = nondet_int(); curbuf = &c;
  sandbox = nondet_int(); textlock = nondet_int(); expr_map_lock = nondet_int();
  msg_calls = 0;
  bool r = undo_allowed(&b);
  const char *want = b.b_p_ma == 0 ? e_modifiable : sandbox != 0 ? e_sandbox
    : (textlock != 0 || (expr_map_lock > 0 && (c.b_flags & 0x80) == 0)) ? e_textlock : NULL;
  assert(r == (want == NULL));
  assert(msg_calls == (want == NULL ? 0 : 1));
  if (want != NULL) assert(msg_fmt == want);
}
void h_corruption_error(void) {
  const char *m = nondet_bool() ? "truncated" : "num_head", *n = "file";
  msg_calls = 0;
  corruption_error(m, n);
  assert(msg_calls == 1 && msg_a1 == m && msg_a2 == n);
  assert(strcmp(msg_fmt, "E825: Corrupted undo file (%s): %s") == 0);
}
