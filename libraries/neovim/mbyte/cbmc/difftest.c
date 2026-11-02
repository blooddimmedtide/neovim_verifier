// Differential test: the compiled upstream functions (gcc -O2 -fsigned-char) against the
// references in spec.h, which the CBMC proofs compare them with. This checks
// that CBMC's reading of the C code matches what a real compiler builds.
// Exhaustive for every int (char2len, char2bytes), every byte (byte2len), and
// every string of up to 3 bytes; random for 4- to 6-byte strings.
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include "spec.h"
#include MBYTE_UTF8_C

static unsigned long fails;
#define CHECK(cond, ...) do { if (!(cond)) { if (fails++ < 10) printf(__VA_ARGS__); } } while (0)

static void str_case(const uint8_t *b, int n) {  // b[0..n-1] nonzero, then NUL
  char s[8] = {0};
  for (int i = 0; i < n; i++) s[i] = (char)b[i];
  CHECK(utf_ptr2len(s) == ref_ptr2len((const uint8_t *)s), "ptr2len %02x..\n", b[0]);
  CHECK(utf_ptr2char(s) == ref_ptr2char((const uint8_t *)s), "ptr2char %02x..\n", b[0]);
  for (int size = 1; size <= 7; size++)
    CHECK(utf_ptr2len_len(s, size) == ref_ptr2len_len((const uint8_t *)s, size), "ptr2len_len %02x.. %d\n", b[0], size);
}

int main(void) {
  unsigned long cases = 0;
  for (int b = 0; b < 256; b++, cases++) CHECK(utf_byte2len(b) == spec_lead_len((uint8_t)b), "byte2len %d\n", b);
  for (int64_t c = INT32_MIN; c <= INT32_MAX; c++, cases++) {
    char buf[6];
    int r = utf_char2bytes((int)c, buf);
    CHECK(r == utf_char2len((int)c), "char2len/char2bytes %ld\n", (long)c);
    if (c < 0) { CHECK(r == 1 && (uint8_t)buf[0] == (uint8_t)(uint32_t)c, "neg %ld\n", (long)c); continue; }
    CHECK(r == spec_enc_len(c) && spec_value((const uint8_t *)buf, r) == (uint32_t)c, "char2bytes %ld\n", (long)c);
  }
  uint8_t b[6];
  for (int n = 0; n <= 3; n++) {
    unsigned long total = 1; for (int i = 0; i < n; i++) total *= 255;
    for (unsigned long x = 0; x < total; x++, cases++) {
      unsigned long y = x; for (int i = 0; i < n; i++) { b[i] = (uint8_t)(1 + y % 255); y /= 255; }
      str_case(b, n);
    }
  }
  srand(12345);
  for (long t = 0; t < 30000000; t++, cases++) {
    int n = 4 + (int)(t % 3);
    for (int i = 0; i < n; i++) {   // bias toward lead and continuation bytes
      int r = rand();
      b[i] = (uint8_t)(i == 0 ? 0xC0 + r % 64 : (r & 3) ? 0x80 + (r >> 2) % 64 : 1 + (r >> 2) % 255);
    }
    str_case(b, n);
  }
  printf("%lu cases, %lu mismatches\n", cases, fails);
  return fails != 0;
}
