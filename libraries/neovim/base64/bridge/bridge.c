// CBMC proof that vim_htobe64/vim_htobe32 are correct: on x86_64,
// `memcpy(&bits_h, p, 8); bits_be = htobe64(bits_h);` yields the big-endian
// value of p[0..7] (and likewise for 4 bytes). This is the full-correctness
// evidence for the two helpers; the WP proof no longer depends on it.
// Checked for every possible byte value, both for Neovim's fallback
// vim_htobe64/vim_htobe32 (included from base64.c) and for glibc's
// htobe64/htobe32, which real Linux builds use (HAVE_BE64TOH).
#include <stdint.h>
#include <string.h>
#include <endian.h>
#include NVIM_BASE64_C   // pulls in the static vim_htobe64 / vim_htobe32

void harness(void) {
  uint8_t p[8];  // nondeterministic: all 2^64 byte patterns
  uint64_t be64 = 0;
  for (int j = 0; j < 8; j++) be64 = (be64 << 8) | p[j];
  uint32_t be32 = 0;
  for (int j = 0; j < 4; j++) be32 = (be32 << 8) | p[j];

  uint64_t h64; memcpy(&h64, p, sizeof h64);
  uint32_t h32; memcpy(&h32, p, sizeof h32);

  __CPROVER_assert(vim_htobe64(h64) == be64, "load64 (Neovim fallback)");
  __CPROVER_assert(vim_htobe32(h32) == be32, "load32 (Neovim fallback)");
  __CPROVER_assert(__bswap_64(h64) == be64, "load64 (glibc htobe64)");
  __CPROVER_assert(__bswap_32(h32) == be32, "load32 (glibc htobe32)");
}
