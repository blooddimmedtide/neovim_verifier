// Every ASCII line up to LMAX bytes, every column inside it, every ASCII quote
// char and every escape set up to EMAX ASCII chars (or NULL). Exact-size objects.
#include <stdlib.h>
#include QUOTE_C
#include "spec.h"
#ifndef LMAX
#define LMAX 6
#endif
#define EMAX 2
unsigned nondet_unsigned(void); int nondet_int(void); _Bool nondet_bool(void);
static char *mk(unsigned n) {
  char *s = malloc(n + 1);
  for (unsigned i = 0; i < n; i++) __CPROVER_assume(s[i] != 0 && (unsigned char)s[i] < 0x80);
  s[n] = 0; return s;
}
static void setup(char **line, int *col, int *q, char **esc, unsigned *ln) {
  *ln = nondet_unsigned(); __CPROVER_assume(*ln <= LMAX);
  *line = mk(*ln);
  unsigned en = nondet_unsigned(); __CPROVER_assume(en <= EMAX);
  *esc = nondet_bool() ? NULL : mk(en);
  *q = nondet_int(); __CPROVER_assume(*q > 0 && *q < 0x80);
  // Precondition (callers use '"', '\'' or '`' with 'quoteescape'): the quote is not an escape char.
  __CPROVER_assume(!is_esc(*esc, (char)*q));
  *col = nondet_int(); __CPROVER_assume(*col >= 0 && (unsigned)*col <= *ln);
}
void h_next(void) {
  char *line, *esc; int col, q; unsigned ln; setup(&line, &col, &q, &esc, &ln);
  __CPROVER_assert(find_next_quote(line, col, q, esc) == ref_next(line, col, q, esc), "next = ref");
}
void h_prev(void) {
  char *line, *esc; int col, q; unsigned ln; setup(&line, &col, &q, &esc, &ln);
  __CPROVER_assert(find_prev_quote(line, col, q, esc) == ref_prev(line, col, q, esc), "prev = ref");
}
