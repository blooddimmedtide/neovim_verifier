// CBMC: offset2bytes vs bytes2offset for every nr in [0, 15*255^3), plus a spec length.
#include <stdint.h>
#include <stdlib.h>
#include "../exhaustive/offset2bytes.c.inc"
#include "../exhaustive/bytes2offset.c.inc"
int nondet_int(void);
int main(void) {
  int nr = nondet_int();
  __CPROVER_assume(nr >= 0 && nr < 15 * 255 * 255 * 255);
  int expect = nr < 0x7f ? 1 : nr < 0x3f * 255 ? 2 : nr < 0x1f * 255 * 255 ? 3 : 4;
  char *buf = malloc(4);          // exact size: a write past 4 bytes fails the bounds check
  __CPROVER_assume(buf != NULL);  // xmalloc never returns NULL
  int n = offset2bytes(nr, buf);
  __CPROVER_assert(n == expect, "minimal length");
  for (int i = 0; i < n; i++) __CPROVER_assert(buf[i] != 0, "no NUL byte");
  char *p = buf;
  int back = bytes2offset(&p);
  __CPROVER_assert(back == nr, "round trip");
  __CPROVER_assert(p == buf + n, "reader consumes exactly n bytes");
  free(buf);
  return 0;
}
