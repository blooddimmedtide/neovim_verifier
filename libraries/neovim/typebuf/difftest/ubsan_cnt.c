// Runs the extracted upstream/fixed del_typebuf() at tb_change_cnt == INT_MAX under UBSan.
// build: see run_ubsan.sh (tb.c is build.py's output; ACSL comments are ignored by gcc)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
void *xmalloc(size_t n) { void *p = malloc(n); if (!p) abort(); return p; }
void *xrealloc(void *p, size_t n) { p = realloc(p, n); if (!p) abort(); return p; }
void xfree(void *p) { free(p); }
void state_no_longer_safe(const char *r) { (void)r; }
void internal_error(const char *w) { (void)w; }
int emsg(const char *s) { (void)s; return 0; }
void setcursor(void) {}
const char e_command_too_complex[] = "E74";
#include "tb.c"
int main(void) {
  init_typebuf();
  char s[] = "abc";
  ins_typebuf(s, REMAP_YES, 0, false, false);
  typebuf.tb_change_cnt = INT_MAX;
  del_typebuf(1, 0);
  printf("tb_change_cnt after del_typebuf: %d\n", typebuf.tb_change_cnt);
  return typebuf.tb_change_cnt == 0;
}
