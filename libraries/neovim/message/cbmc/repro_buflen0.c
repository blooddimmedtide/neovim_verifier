// Reproducer: trunc_string writes buf[-1] when buflen == 0 and s is short.
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#define NUL '\0'
static int ptr2cells(const char *p) { unsigned char c = (unsigned char)*p; return (c < 0x20 || c == 0x7f) ? 2 : 1; }
static int utfc_ptr2len(const char *p) { return *p == NUL ? 0 : 1; }
static int utf_head_off(const char *base, const char *p) { (void)base; (void)p; return 0; }
#include "trunc_string.c"
int main(void) { char *buf = malloc(1); trunc_string("ab", buf, 0, 0); free(buf); return 0; }
