#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#define NUL '\000'
#include "fn_global.c"
#include "spec.h"
#ifndef N
#define N 10
#endif
long nondet_long(void);
char nondet_char(void);
int main(void)
{
  long len = nondet_long();
  __CPROVER_assume(len >= 0 && len <= N);
  char *s = malloc(len + 1);   // exact size: reading past the NUL fails the pointer check
  __CPROVER_assume(s != NULL);  // callers pass a live command line (xmalloc never fails)
  for (long i = 0; i < len; i++) { s[i] = nondet_char(); __CPROVER_assume(s[i] != NUL); }
  s[len] = NUL;
  const char *r = find_cmd_after_global_cmd(s);
  long e = ref_global(s, len);
  if (e < 0) __CPROVER_assert(r == NULL, "no closing delimiter -> NULL");
  else __CPROVER_assert(r == s + e, "returns char after closing delimiter");
  return 0;
}
