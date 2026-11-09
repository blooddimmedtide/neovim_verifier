// Spec (from the doc comment "Move a long integer into a four byte character array",
// used for machine independence of block 0): the four bytes are the low 32 bits of n,
// least significant first; char_to_long reads them back as the unsigned 32-bit value.
// Exact-size 4-byte objects, so any out-of-bounds access fails the check.
#include <assert.h>
#include <stdint.h>
long nondet_long(void);
char nondet_char(void);
int main(void) {
  long n = nondet_long();
  char s[4];
  long_to_char(n, s);
  uint32_t low = (uint32_t)(unsigned long)n;
  for (int k = 0; k < 4; k++)
    assert((uint8_t)s[k] == (uint8_t)(low >> (8 * k)));
  assert(char_to_long(s) == (long)low);          // round trip of the low 32 bits
  char t[4] = { nondet_char(), nondet_char(), nondet_char(), nondet_char() };
  long v = char_to_long(t);
  assert(v >= 0 && v <= 4294967295L);
  assert(v == (long)((uint32_t)(uint8_t)t[0] | (uint32_t)(uint8_t)t[1] << 8
                     | (uint32_t)(uint8_t)t[2] << 16 | (uint32_t)(uint8_t)t[3] << 24));
  return 0;
}
