// put_bytes: writes `len` bytes of `number`, most significant first ("Writes a number to file
// "fd", most significant bit first, in "len" bytes"; returns false on a write error).
// put_time: "Writes time_t to file "fd" in 8 bytes. @return FAIL when the write failed."
// putc/fwrite are modelled: each call may fail (nondet); successful bytes are recorded.
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <assert.h>
typedef struct { int dummy; } FILE;
#define EOF (-1)
#define OK 1
#define FAIL 0
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
typedef long time_t;
static unsigned char outb[16]; static size_t nout; static bool failed;
_Bool nondet_bool(void); size_t nondet_size(void); uintmax_t nondet_umax(void); long nondet_long(void);
int putc(int c, FILE *f) { if (nondet_bool()) { failed = true; return EOF; } assert(nout < 16); outb[nout++] = (unsigned char)c; return (unsigned char)c; }
size_t fwrite(const void *p, size_t sz, size_t n, FILE *f) {
  size_t k = nondet_size(); __CPROVER_assume(k <= n); // short write allowed
  for (size_t i = 0; i < k * sz; i++) outb[nout++] = ((const unsigned char *)p)[i];
  if (k < n) failed = true; return k; }
// time_to_bytes from memory.c ("most significant byte first"), modelled per its contract.
static void time_to_bytes(time_t t, uint8_t buf[8]) { for (int i = 7; i >= 0; i--) { buf[i] = (uint8_t)t; t = (time_t)((uint64_t)t >> 8); } }
#include PUT_C
static FILE F;
void h_put_bytes(void) {
  uintmax_t number = nondet_umax(); size_t len = nondet_size();
  // Precondition: 1 <= len (asserted by the function) and len <= 8 (sizeof uintmax_t);
  // larger len would shift by >= 64 bits. All 21 callers pass 1, 2, 3 or 4.
  __CPROVER_assume(len >= 1 && len <= 8);
  bool r = put_bytes(&F, number, len);
  assert(r == !failed);
  if (r) { assert(nout == len);
    for (size_t j = 0; j < len; j++) assert(outb[j] == (unsigned char)(number >> (8 * (len - 1 - j)))); }
}
void h_put_time(void) {
  time_t t = nondet_long();
  int r = put_time(&F, t);
  assert(r == (failed ? FAIL : OK));   // documented contract
}
