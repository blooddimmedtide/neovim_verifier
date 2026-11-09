// CBMC harness: inmacro(opt, s) against ref_inmacro for every option string of
// up to OPTMAX bytes and every line of up to LINEMAX bytes. Both live in
// exact-size objects, so reading past either NUL fails the bounds check.
#include <stdlib.h>
#include INMACRO_C
#include "spec.h"
#ifndef OPTMAX
#define OPTMAX 12
#endif
#ifndef LINEMIN
#define LINEMIN 0
#endif
#ifndef LINEMAX
#define LINEMAX 3
#endif
unsigned nondet_unsigned(void);
void h_inmacro(void) {
  unsigned on = nondet_unsigned(), ln = nondet_unsigned();
  __CPROVER_assume(on <= OPTMAX && ln >= LINEMIN && ln <= LINEMAX);
  char *opt = malloc(on + 1), *s = malloc(ln + 1);
  for (unsigned i = 0; i < on; i++) __CPROVER_assume(opt[i] != '\0');
  for (unsigned i = 0; i < ln; i++) __CPROVER_assume(s[i] != '\0');
  opt[on] = '\0'; s[ln] = '\0';
  bool r = inmacro(opt, s);
  __CPROVER_assert(r == ref_inmacro(opt, s), "inmacro matches reference");
}
