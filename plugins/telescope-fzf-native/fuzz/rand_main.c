// Random driver for fuzz.c (no libFuzzer runtime here): builds inputs from
// fzf's pattern syntax characters, letters and high bytes, and runs them under
// ASan/UBSan. Usage: ./rf <seconds> [seed]
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int LLVMFuzzerTestOneInput(const uint8_t *d, size_t n);

static uint64_t s = 1;
static uint64_t rnd(void) { s ^= s << 13; s ^= s >> 7; s ^= s << 17; return s; }

int main(int argc, char **argv) {
  int secs = argc > 1 ? atoi(argv[1]) : 60;
  s = argc > 2 ? strtoull(argv[2], NULL, 0) : 88172645463325252ull;
  const char alpha[] = "aAbBcC_-/. '^$!|\\\t\x01";
  time_t end = time(NULL) + secs;
  unsigned long runs = 0;
  uint8_t buf[512];
  while (time(NULL) < end) {
    for (int k = 0; k < 1000; k++, runs++) {
      size_t n = 2 + rnd() % (rnd() % 4 == 0 ? 500 : 40);
      for (size_t i = 0; i < n; i++) {
        uint64_t r = rnd();
        buf[i] = (r & 3) ? (uint8_t)alpha[(r >> 2) % (sizeof alpha - 1)] : (uint8_t)(r >> 8);
      }
      LLVMFuzzerTestOneInput(buf, n);
    }
  }
  printf("%lu runs, no sanitizer report\n", runs);
  return 0;
}
