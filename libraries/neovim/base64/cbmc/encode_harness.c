// Proves, for every input up to MAX_LEN bytes:
//  - base64_encode has no out-of-bounds access, overflow, or UB;
//  - its output equals the RFC 4648 reference, byte for byte, and is NUL-terminated.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "nvim/base64.h"
#include "spec.h"
#ifndef MAX_LEN
#define MAX_LEN 17
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
  char *out = base64_encode(src, n);
  size_t out_len = ((n + 2) / 3) * 4;
  for (size_t i = 0; i < out_len; i++) {
    __CPROVER_assert(out[i] == ref_enc_char(i, (const uint8_t *)src, n), "matches RFC 4648");
  }
  __CPROVER_assert(out[out_len] == '\0', "NUL-terminated");
  free(out);
  free(src);
}
