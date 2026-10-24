// Proves decode(encode(x)) == x for every input up to MAX_LEN bytes.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "nvim/base64.h"
#ifndef MAX_LEN
#define MAX_LEN 10
#endif
void harness(void) {
  size_t n;
  #ifdef EXACT_LEN
  __CPROVER_assume(n == EXACT_LEN);
#else
  __CPROVER_assume(n <= MAX_LEN);
#endif
  char *src = malloc(n ? n : 1);
  __CPROVER_assume(src != NULL);
  char *enc = base64_encode(src, n);
  size_t enc_len = ((n + 2) / 3) * 4;
  size_t out_len;
  char *dec = base64_decode(enc, enc_len, &out_len);
  __CPROVER_assert(dec != NULL, "decode accepts encoder output");
  __CPROVER_assert(out_len == n, "length preserved");
  for (size_t i = 0; i < n; i++) __CPROVER_assert(dec[i] == src[i], "bytes preserved");
  free(dec);
  free(enc);
  free(src);
}
