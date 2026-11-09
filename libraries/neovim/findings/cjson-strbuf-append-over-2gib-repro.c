// Build: gcc -O1 -fsanitize=undefined -fno-sanitize-recover=undefined -I src/cjson \
//        cjson-strbuf-append-over-2gib-repro.c src/cjson/strbuf.c -o big && ./big
// strbuf_append_string with a string longer than INT_MAX bytes.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "strbuf.h"
int main(void) {
  size_t n = (size_t)INT32_MAX + 2;
  char *str = malloc(n + 1); memset(str, 'x', n); str[n] = 0;
  strbuf_t s; strbuf_init(&s, 0);
  strbuf_append_string(&s, str);
  printf("length %zu (want %zu)\n", strbuf_length(&s), n);
  return 0;
}
