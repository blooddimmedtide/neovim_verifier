// Reproducer for cp-bounds-over-2gib.md. Build: python3 -I ../mbyte/cbmc/build.py <nvim> m.c && gcc -O0 -g -fsanitize=address,undefined -DMBYTE_UTF8_C=\"m.c\" cp-bounds-over-2gib-repro.c
// Run: ./a.out 2147483649   (out-of-bounds read)   ./a.out 4294967298 x   (wrong result)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include MBYTE_UTF8_C
int main(int argc, char **argv) {
  size_t d = strtoull(argv[1], NULL, 0);
  unsigned char *buf = malloc(d + 8);
  if (!buf) { perror("malloc"); return 2; }
  memset(buf, 0x80, d + 8);               // all continuation bytes
  if (argc > 2) {                          // a valid 3-byte char ending at p: E2 82 AC (euro sign)
    buf[d - 2] = 0xE2; buf[d - 1] = 0x82; buf[d] = 0xAC;
  }
  CharBoundsOff r = utf_cp_bounds_len((char *)buf, (char *)buf + d, 1 + (argc > 2));
  printf("d=%zu begin_off=%d end_off=%d\n", d, r.begin_off, r.end_off);
  return 0;
}
