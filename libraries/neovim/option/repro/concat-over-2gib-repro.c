// Reproducer: stropt_concat_with_comma (option.c, upstream 7b87ce8) with an origval of
// 2^31 + 16 bytes, as `:set wildignore+=b` does once 'wildignore' is that long.
// The function text in fn.c is copied verbatim; build with ASan.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define NUL '\000'
#define STRMOVE(d, s) memmove((d), (s), strlen(s) + 1)
typedef enum { OP_NONE = 0, OP_ADDING, OP_PREPENDING, OP_REMOVING } set_op_T;
enum { kOptFlagComma = 1 << 10, kOptFlagOneComma = (1 << 11) | kOptFlagComma };
#include "fn.c"
int main(void) {
  size_t n = ((size_t)1 << 31) + 16;
  char *orig = malloc(n + 1);
  memset(orig, 'a', n); orig[n] = 0;
  char *newval = malloc(n + 3);   // room for origval + "," + "b" + NUL, as stropt_copy_value allocates
  strcpy(newval, "b");
  stropt_concat_with_comma(orig, newval, OP_ADDING, kOptFlagComma);
  printf("ok: result length %zu (expected %zu)\n", strlen(newval), n + 2);
  return 0;
}
