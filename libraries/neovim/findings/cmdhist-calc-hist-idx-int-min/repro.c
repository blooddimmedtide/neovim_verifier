// Reproducer: calc_hist_idx(type, INT_MIN), reachable from Vimscript histget('cmd', -2147483648)
// and histdel('cmd', -2147483648). Build: gcc -O0 -fsanitize=undefined,address repro.c
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>
typedef struct { int hisnum; char *hisstr; size_t hisstrlen; } histentry_T;
#define HIST_COUNT 5
static histentry_T *history[HIST_COUNT]; static int hisidx[HIST_COUNT]; static int hislen;
static int calc_hist_idx(int histype, int num)
{
  int i;
  if (hislen == 0 || histype < 0 || histype >= HIST_COUNT
      || (i = hisidx[histype]) < 0 || num == 0) {
    return -1;
  }
  histentry_T *hist = history[histype];
  if (num > 0) {
    return -1;  // not exercised here
  } else if (-num <= hislen) {
    i += num + 1;
    if (i < 0) {
      i += hislen;
    }
    if (hist[i].hisstr != NULL) {
      return i;
    }
  }
  return -1;
}
int main(void)
{
  static char s[] = "x";
  hislen = 50; history[0] = calloc(50, sizeof(histentry_T)); hisidx[0] = 0;
  history[0][0].hisstr = s;
  printf("%d\n", calc_hist_idx(0, INT_MIN));
}
