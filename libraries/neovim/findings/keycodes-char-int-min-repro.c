// Reproducer: find_special_key turns <Char-0x80000000> into key = (int)n = INT_MIN,
// then special_to_buf / simplify_key evaluate KEY2TERMCAP0(key) = (-(key)) & 0xff.
#include <limits.h>
#include <stdio.h>
#include <stdint.h>
#define KEY2TERMCAP0(x)         ((-(x)) & 0xff)
#define KEY2TERMCAP1(x)         (((unsigned)(-(x)) >> 8) & 0xff)
int main(int argc, char **argv) {
  uint64_t n = 0x80000000u;   // vim_str2nr result for "0x80000000"
  volatile int key = (int)n;  // find_special_key: key = (int)n;
  if (key < 0) {              // IS_SPECIAL(key) in special_to_buf
    printf("%d %d\n", KEY2TERMCAP0(key), KEY2TERMCAP1(key));
  }
  return 0;
}
