#include <stdlib.h>
#include "spec.h"
#include FILEIO_BOM_C
int nondet_int(void);
// Precondition (documented at the only caller, fileio.c readfile: "no BOM
// detection in a short file"): size >= 2. The buffer is exactly size bytes.
void h_check_for_bom(void) {
  int size = nondet_int();
  __CPROVER_assume(size >= 2);
  char *p = malloc((size_t)size);
  int flags = nondet_int();
  int len = -7, rlen;
  char *got = check_for_bom(p, size, &len, flags);
  const char *want = ref_bom((const uint8_t *)p, size, flags, &rlen);
  assert(len == rlen);
  assert((got == 0) == (want == 0));
  if (got) assert(strcmp(got, want) == 0);
  if (got) assert(len <= size);   // the BOM never runs past the data
}
