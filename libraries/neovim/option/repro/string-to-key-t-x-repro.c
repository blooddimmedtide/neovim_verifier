// Reproducer: string_to_key("<t_x") (option.c, upstream 7b87ce8) reads one byte past the
// string's NUL, as `:set cedit=<t_x` or `:set wildchar=<t_x` does. fn.c is verbatim upstream.
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#define TERMCAP2KEY(a, b)       (-((a) + ((int)(b) << 8)))
#define CTRL_CHR(x)             (TOUPPER_ASC(x) ^ 0x40)
#define TOUPPER_ASC(c) (((c) < 'a' || (c) > 'z') ? (c) : (c) - ('a' - 'A'))
#define K_ZERO 1
enum { FSK_KEYCODE = 1, FSK_KEEP_X_KEY = 2, FSK_SIMPLIFY = 8 };
static int find_special_key(const char **s, size_t l, int *m, int f, bool *d) { (void)s; (void)l; (void)f; (void)d; *m = 0; return 0; }
#include "fn.c"
int main(void) {
  char *v = malloc(5);   // option values are allocated to their exact length
  memcpy(v, "<t_x", 5);
  printf("key %d\n", string_to_key(v));
  free(v);
  return 0;
}
