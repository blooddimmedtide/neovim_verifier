// Proves, for every input string up to MAX_LEN bytes (any byte values):
//  - base64_decode has no out-of-bounds access, overflow, or UB;
//  - on success, re-encoding the result gives back exactly the input
//    (so the decoder accepts only canonical Base64);
//  - on failure, it returns NULL with length 0.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "nvim/base64.h"
#include "spec.h"
#ifndef MAX_LEN
#define MAX_LEN 12
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
  size_t out_len;
  char *out = base64_decode(src, n, &out_len);
  if (out == NULL) {
    __CPROVER_assert(out_len == 0, "failure reports length 0");
    free(src);
    return;
  }
  __CPROVER_assert(n == ((out_len + 2) / 3) * 4, "length relation");
  for (size_t i = 0; i < n; i++) {
    __CPROVER_assert(src[i] == ref_enc_char(i, (const uint8_t *)out, out_len),
                     "accepted input is the canonical encoding of the output");
  }
  free(out);
  free(src);
}
