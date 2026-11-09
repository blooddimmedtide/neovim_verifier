#include <stdlib.h>
#include <assert.h>
#include MENU_C
#include "spec.h"
#ifndef N
#define N 12
#endif
char nondet_char(void); size_t nondet_size(void);
/* Exact-size NUL-terminated string of nondeterministic bytes, length < N. */
static char *mkstr(void) {
  size_t n = nondet_size(); __CPROVER_assume(n < N);
  char *s = malloc(n + 1);
  for (size_t i = 0; i < n; i++) { s[i] = nondet_char(); __CPROVER_assume(s[i] != 0); }
  s[n] = 0; return s; }
void h_winbar(void) { char *s = mkstr(); assert(menu_is_winbar(s) == r_prefix(s, "WinBar", 6)); }
void h_popup(void) { char *s = mkstr(); assert(menu_is_popup(s) == r_prefix(s, "PopUp", 5)); }
void h_toolbar(void) { char *s = mkstr(); assert(menu_is_toolbar(s) == r_prefix(s, "ToolBar", 7)); }
void h_menubar(void) { char *s = mkstr();
  assert(menu_is_menubar(s) == (!r_prefix(s, "PopUp", 5) && !r_prefix(s, "ToolBar", 7)
                                && !r_prefix(s, "WinBar", 6) && s[0] != ']')); }
void h_separator(void) { char *s = mkstr(); size_t n = r_len(s);
  assert(menu_is_separator(s) == (n >= 1 && s[0] == '-' && s[n - 1] == '-')); }
void h_hidden(void) { char *s = mkstr();
  assert(menu_is_hidden(s) == (s[0] == ']' || (r_prefix(s, "PopUp", 5) && r_len(s) > 5))); }
void h_namecmp(void) { char *a = mkstr(); char *b = mkstr();
  assert(menu_namecmp(a, b) == r_samepart(a, b)); }
void h_skip_part(void) { char *s = mkstr(); char *q = menu_skip_part(s);
  assert(q == s + r_skip(s)); }
