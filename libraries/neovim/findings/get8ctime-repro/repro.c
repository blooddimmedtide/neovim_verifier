// Reproducer: get8ctime (src/nvim/fileio.c, upstream 7b87ce8) on a timestamp whose first byte
// is >= 0x80, as a crafted undo file (uh_time / seq_time) or .sug spell file can hold.
// Build: gcc -O0 -fsanitize=undefined -fno-sanitize-recover=all repro.c && ./a.out
#include <stdio.h>
#include <time.h>
time_t get8ctime(FILE *fd)   // verbatim upstream body
{
  time_t n = 0;

  for (int i = 0; i < 8; i++) {
    const int c = getc(fd);
    if (c == EOF) {
      return -1;
    }
    n = (n << 8) + c;
  }
  return n;
}
int main(void) {
  FILE *f = tmpfile();
  const unsigned char b[8] = { 0x80, 0, 0, 0, 0, 0, 0, 1 };
  fwrite(b, 1, 8, f); rewind(f);
  printf("%lld\n", (long long)get8ctime(f));
  return 0;
}
