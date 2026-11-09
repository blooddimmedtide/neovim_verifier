// Reproducer: tv_blob_slice() (src/nvim/eval/typval.c, upstream 7b87ce8) with an empty blob,
// exclusive = true (Vimscript slice()) and end index v:numbermin: `n2--` overflows int64_t.
// Build: gcc -O0 -fsanitize=signed-integer-overflow -fno-sanitize-recover repro_slice_overflow.c
// The arithmetic below is copied verbatim from tv_blob_slice; allocation is not reached.
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
typedef int64_t varnumber_T;
static int slice_bounds(int len, varnumber_T n1, varnumber_T n2, bool exclusive)
{
  if (n1 < 0) {
    n1 = len + n1;
    if (n1 < 0) {
      n1 = 0;
    }
  }
  if (n2 < 0) {
    n2 = len + n2;
  } else if (n2 >= len) {
    n2 = len - (exclusive ? 0 : 1);
  }
  if (exclusive) {
    n2--;
  }
  return n1 >= len || n2 < 0 || n1 > n2;  // 1 = empty result
}
int main(void)
{
  // :echo slice(0z, 0, v:numbermin)
  printf("empty=%d\n", slice_bounds(0, 0, INT64_MIN, true));
  return 0;
}
