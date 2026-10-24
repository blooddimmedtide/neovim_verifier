// Reads records from stdin: one byte op ('e' or 'd'), 4-byte little-endian
// length, then the bytes. Writes for each: 'N' (NULL) or 'Y' + 8-byte length +
// output bytes. Compiled once against pristine base64.c and once against the
// tool-patched + annotated file WP proves, so the two can be compared.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include NVIM_BASE64_C

int main(void) {
  int op;
  while ((op = getchar()) != EOF) {
    uint8_t l[4];
    if (fread(l, 1, 4, stdin) != 4) return 1;
    size_t n = l[0] | l[1] << 8 | l[2] << 16 | (size_t)l[3] << 24;
    char *in = malloc(n ? n : 1);
    if (fread(in, 1, n, stdin) != n) return 1;
    char *out; size_t out_len = 0;
    if (op == 'e') { out = base64_encode(in, n); out_len = out ? strlen(out) : 0; }
    else out = base64_decode(in, n, &out_len);
    if (!out) putchar('N');
    else { putchar('Y'); uint64_t L = out_len; fwrite(&L, 8, 1, stdout); fwrite(out, 1, out_len, stdout); xfree(out); }
    free(in);
  }
  return 0;
}
