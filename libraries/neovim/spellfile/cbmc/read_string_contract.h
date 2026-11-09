// read_string's contract as proved by ../wp/run_wp.sh (Frama-C WP, every cnt, no admits):
// enough bytes left -> a valid (cnt+1)-byte block holding the next cnt bytes and a NUL,
// position advanced by cnt; otherwise NULL and position at end of file.
// The assume below states that proved postcondition at one index ghost_j, which the harness
// picks nondeterministically before the call (so it covers every index); it is the only
// assume in the composed run.
static size_t ghost_j;
static char *read_string(FILE *fd, size_t cnt) {
  if (fd->len - fd->pos < cnt) { fd->pos = fd->len; fd->eof = true; return NULL; }
  char *s = xmallocz(cnt);
  size_t p0 = fd->pos;
  __CPROVER_assume(ghost_j >= cnt || s[ghost_j] == (char)fd->data[p0 + ghost_j]);
  fd->pos = p0 + cnt;
  return s;
}
