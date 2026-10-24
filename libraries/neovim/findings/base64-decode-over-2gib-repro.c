#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "nvim/base64.h"
int main(void) {
  size_t n = (1ul << 31) + 4;
  char *s = malloc(n);
  memset(s, 'A', n);
  s[1ul << 31] = '=';          // '=' at index 2^31, followed by "AAA"
  size_t out_len = 0;
  char *d = base64_decode(s, n, &out_len);
  printf("input \"...AAAA=AAA\" (len 2^31+4): %s, out_len=%zu\n", d ? "ACCEPTED" : "rejected", out_len);
  // Small control: same shape, short input.
  char t[] = "AAAA=AAA";
  char *e = base64_decode(t, 8, &out_len);
  printf("input \"AAAA=AAA\" (len 8): %s\n", e ? "ACCEPTED" : "rejected");
  return 0;
}
