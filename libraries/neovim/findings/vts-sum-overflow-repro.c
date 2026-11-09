// Reproducer: get_vts / get_vts_sum copied verbatim from src/nvim/ops.c at 7b87ce8.
// gcc -O0 -fsanitize=undefined -fno-sanitize-recover=all vts-sum-overflow-repro.c && ./a.out
#include <stdio.h>
static int get_vts(const int *vts_array, int index)
{
  int ts;

  if (index < 1) {
    ts = 0;
  } else if (index <= vts_array[0]) {
    ts = vts_array[index];
  } else {
    ts = vts_array[vts_array[0]];
  }

  return ts;
}

static int get_vts_sum(const int *vts_array, int index)
{
  int sum = 0;
  int i;

  // Perform the summation for indices within the actual array.
  for (i = 1; i <= index && i <= vts_array[0]; i++) {
    sum += vts_array[i];
  }

  // Add tabstops whose indices exceed the actual array.
  if (i <= index) {
    sum += vts_array[vts_array[0]] * (index - vts_array[0]);
  }

  return sum;
}
int main(void) {
  // 'shiftwidth'=0, 'vartabstop'=8 (vts_array = {1, 8}); Visual 999999999> (count is capped at 999999999)
  // get_new_vts_indent right shift computes get_vts_sum(vts_array, vtsi + amount) with vtsi = 0 at indent 0.
  int vts[2] = {1, 8};
  printf("%d\n", get_vts_sum(vts, 0 + 999999999));
  return 0;
}
