// Exhaustive check over every int nr (all 2^32 values) of offset2bytes, the .sug <sugnr>
// writer, against an independent spec from the format comment in spellfile.c:
// "stored as an offset ... in as few bytes as possible", no NUL bytes (a NUL ends <sugline>),
// and read back by bytes2offset (spellsuggest.c, the reader).
// Spec (independent): base-255 digits d_i = digit+1 in 1..255, so no NUL; lead byte tags
// 0xxxxxxx (1 byte, value < 0x7f), 10xxxxxx (2), 110xxxxx (3), 1110xxxx (4: reader keeps 4 bits).
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>
#include "offset2bytes.c.inc"
#include "bytes2offset.c.inc"

static int spec_len(long long nr) {   // minimal length, or 0 if not representable
  if (nr < 0) return 0;
  if (nr < 0x7f) return 1;                         // lead 1..0x7f
  if (nr < 0x3fLL * 255) return 2;                 // lead digit 1..0x3f
  if (nr < 0x1fLL * 255 * 255) return 3;
  if (nr < 0x0fLL * 255 * 255 * 255) return 4;     // reader masks lead with 0x0f
  return 0;
}

int main(void) {
  unsigned long long ok = 0, bad_neg = 0, bad_big = 0, nul = 0;
  long long first_big = -1, first_neg_nul = 0;
  for (long long v = INT_MIN; v <= INT_MAX; v++) {
    int nr = (int)v;
    char buf[8]; memset(buf, 0x55, sizeof buf);
    int n = offset2bytes(nr, buf);
    int has_nul = 0;
    for (int i = 0; i < n; i++) if (buf[i] == 0) has_nul = 1;
    char *p = buf; int back = bytes2offset(&p);
    int expect = spec_len(v);
    int good = expect != 0 && n == expect && !has_nul && back == nr && p == buf + n
               && buf[n] == 0x55;
    if (expect != 0) {
      if (!good) { printf("FAIL in-range nr=%d n=%d expect=%d back=%d\n", nr, n, expect, back); return 1; }
      ok++;
    } else if (nr < 0) {
      bad_neg++; if (has_nul && !nul++) first_neg_nul = nr;
    } else {
      if (back != nr || has_nul) { bad_big++; if (first_big < 0) first_big = nr; }
    }
    if (n < 1 || n > 4) { printf("FAIL length %d at %d\n", n, nr); return 1; }
  }
  printf("in-range (0 <= nr < %lld): %llu values, all correct\n", 0x0fLL*255*255*255, ok);
  printf("nr >= that bound: %llu values decode wrongly; first %lld\n", bad_big, first_big);
  printf("nr < 0: %llu values (outside spec); %llu produce a NUL byte, first %lld\n", bad_neg, nul, first_neg_nul);
  return 0;
}
