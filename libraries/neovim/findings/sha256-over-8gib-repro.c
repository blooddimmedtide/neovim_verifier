// Reproducer: SHA-256 of n bytes of 'a' through Neovim's sha256.c in one update.
// Build with small stub headers next to it (inc/): nvim/ascii_defs.h (#define NUL 0),
// nvim/memory.h (#include <string.h> and #define STRCPY(d, s) strcpy((char *)(d), (char *)(s))),
// nvim/sha256.h (from Neovim), sha256.c.generated.h (empty), sha256.h.generated.h (prototypes
// of sha256_start, sha256_update, sha256_finish, sha256_self_test):
//   gcc -O2 -Iinc -Iinc/nvim src/nvim/sha256.c sha256-over-8gib-repro.c -o big && ./big 8589934597
// Compare: python3 -c "import hashlib; print(hashlib.sha256(b'a' * 8589934597).hexdigest())"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "nvim/sha256.h"
int main(int argc, char **argv) {
  size_t n = strtoull(argv[1], 0, 0);
  uint8_t *b = malloc(n); memset(b, 'a', n);
  context_sha256_T c; uint8_t d[32];
  sha256_start(&c); sha256_update(&c, b, n); sha256_finish(&c, d);
  for (int i = 0; i < 32; i++) printf("%02x", d[i]); printf("\n");
  return 0;
}
