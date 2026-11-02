// Differential test driver: random messages hashed through Neovim's sha256.c with random
// update splits (and sha256_bytes with a random salt split); prints "hex-message digest"
// lines for difftest.py to check against Python's hashlib. Also runs sha256_self_test.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "nvim/sha256.h"
static unsigned long long s;
static unsigned rnd(void) { s ^= s << 13; s ^= s >> 7; s ^= s << 17; return (unsigned)(s >> 11); }
int main(int argc, char **argv) {
  int n = atoi(argv[1]); s = strtoull(argv[2], 0, 0);
  if (!sha256_self_test() || !sha256_self_test()) { printf("SELFTEST FAILED\n"); return 1; }
  static uint8_t m[1200];
  for (int it = 0; it < n; it++) {
    size_t len = rnd() % (rnd() % 4 ? 200 : 1200);
    for (size_t i = 0; i < len; i++) m[i] = (uint8_t)rnd();
    context_sha256_T c; uint8_t d[32];
    sha256_start(&c);
    size_t p = 0;
    while (p < len) { size_t k = rnd() % (len - p + 1); sha256_update(&c, m + p, k); p += k; if (rnd() % 8 == 0) sha256_update(&c, m, 0); }
    sha256_finish(&c, d);
    for (size_t i = 0; i < len; i++) printf("%02x", m[i]);
    printf(" ");
    for (int i = 0; i < 32; i++) printf("%02x", d[i]);
    printf("\n");
    size_t cut = len ? rnd() % (len + 1) : 0;
    const char *h = sha256_bytes(m, cut, rnd() % 2 ? m + cut : NULL, len - cut);
    // with a NULL salt only the first cut bytes are hashed
    printf("B %zu %s\n", cut, h);
  }
  return 0;
}
