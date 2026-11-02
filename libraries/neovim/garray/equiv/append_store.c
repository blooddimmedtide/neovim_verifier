// Tool patch check (wp/tool_patches.py): GA_APPEND(uint8_t, gap, c) stores
//   ((uint8_t *)(gap)->ga_data)[(gap)->ga_len] = (c);
// and the WP copy stores
//   ((char *)(gap)->ga_data)[(gap)->ga_len] = (char)(c);
// For every byte value c, every index and every buffer content, both leave the
// same bytes. No __CPROVER_assume; run for signed and unsigned char.
#include <stdint.h>
#include <string.h>
#define N 4
uint8_t nondet_u8(void);
unsigned nondet_unsigned(void);
int main(void)
{
  unsigned char a[N], b[N];
  for (int k = 0; k < N; k++) { a[k] = b[k] = nondet_u8(); }
  uint8_t c = nondet_u8();
  unsigned len = nondet_unsigned() % N;
  void *da = a, *db = b;
  ((uint8_t *)da)[len] = (c);              // original
  ((char *)db)[len] = (char)(c);           // tool-patched
  __CPROVER_assert(memcmp(a, b, N) == 0, "same bytes");
  return 0;
}
