// Build: gcc -O2 -I <nvim>/src/mpack mpack-chunk-over-4gib-repro.c <nvim>/src/mpack/mpack_core.c
// Reproducer: mpack_read passes a payload chunk of length 0 (no progress) when
// the remaining input is a multiple of 4 GiB. The payload is never read, so a
// reserved-but-untouched mapping is enough.
#include <stdio.h>
#include <sys/mman.h>
#include "mpack_core.h"
int main(void) {
  size_t total = 5 + ((size_t)1 << 32);   // bin 32 header + 4 GiB of payload
  char *buf = mmap(NULL, total, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE, -1, 0);
  if (buf == MAP_FAILED) { perror("mmap"); return 2; }
  buf[0] = (char)0xc6; buf[1] = buf[2] = buf[3] = buf[4] = (char)0xff;   // bin 32, length 0xffffffff
  mpack_tokbuf_t tb; mpack_tokbuf_init(&tb);
  const char *p = buf; size_t len = total; mpack_token_t tok;
  int st = mpack_read(&tb, &p, &len, &tok);
  printf("header: status %d type %d length %u, %zu bytes left\n", st, tok.type, tok.length, len);
  for (int i = 0; i < 3; i++) {
    st = mpack_read(&tb, &p, &len, &tok);
    printf("call %d: status %d type %d chunk length %u, %zu bytes left\n", i, st, tok.type, tok.length, len);
  }
  return 0;
}
