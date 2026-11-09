// CBMC proof of sha256_bytes: it hashes buf, then salt when salt != NULL, in one fresh
// context, and returns the 64 lowercase hex digits of the digest plus a NUL.
// goto-instrument --replace-calls swaps sha256_start/update/finish/self_test for the
// recorders below (start/update/finish are proved separately; sha256_self_test only sets
// its own statics and overwrites the static hex buffer, which sha256_bytes rewrites whole).
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "nvim/sha256.h"

size_t nondet_size(void);
uint8_t nondet_u8(void);
static int seq;                       // 0 start, 1 buf hashed, 2 salt hashed, 3 finished
static context_sha256_T *the_ctx;
static const uint8_t *exp_buf, *exp_salt;
static size_t exp_buf_len, exp_salt_len;
static uint8_t made[SHA256_SUM_SIZE];
static context_sha256_T saved;   // the context as the last recorder left it (shadow)
// Each recorder gives the context arbitrary new contents and records them; the next one
// checks sha256_bytes did not change the context in between.
#define CTX_KEPT(c) __CPROVER_assert((c)->total[0] == saved.total[0] && (c)->total[1] == saved.total[1] \
  && __CPROVER_array_equal((c)->state, saved.state) && __CPROVER_array_equal((c)->buffer, saved.buffer), \
  "context unchanged between calls")
#define CTX_NEW(c) do { __CPROVER_havoc_object(c); saved = *(c); } while (0)

void rec_start(context_sha256_T *ctx) { __CPROVER_assert(seq == 0, "start first"); the_ctx = ctx; seq = 1; CTX_NEW(ctx); }
void rec_update(context_sha256_T *ctx, const uint8_t *in, size_t len) {
  __CPROVER_assert(ctx == the_ctx, "same context");
  CTX_KEPT(ctx);
  if (seq == 1) { __CPROVER_assert(in == exp_buf && len == exp_buf_len, "buf hashed first"); seq = 2; }
  else { __CPROVER_assert(seq == 2 && exp_salt != NULL && in == exp_salt && len == exp_salt_len, "then salt"); seq = 3; }
  CTX_NEW(ctx);
}
void rec_finish(context_sha256_T *ctx, uint8_t digest[SHA256_SUM_SIZE]) {
  __CPROVER_assert(ctx == the_ctx && seq == (exp_salt != NULL ? 3 : 2), "finish after the input");
  CTX_KEPT(ctx);
  for (int i = 0; i < SHA256_SUM_SIZE; i++) digest[i] = made[i] = nondet_u8();
  seq = 4;
}
bool rec_self_test(void) { bool b; return b; }

// C library model (trusted): snprintf(s, n, "%02x", v) for n >= 3 and 0 <= v <= 0xff writes
// two lowercase hex digits and a NUL (C11 7.21.6.1). CBMC's variadic support cannot read
// the promoted argument, so calls are routed to this fixed-arity model by a macro (stdio.h
// is already included above, so its declaration of snprintf is unaffected).
static int vp_snprintf(char *s, size_t n, const char *fmt, int v) {
  __CPROVER_assert(fmt[0] == '%' && fmt[1] == '0' && fmt[2] == '2' && fmt[3] == 'x' && fmt[4] == 0, "only %02x used");
  __CPROVER_assert(0 <= v && v <= 0xff && n >= 3, "two digits fit");
  const char *hx = "0123456789abcdef";
  s[0] = hx[v >> 4]; s[1] = hx[v & 15]; s[2] = 0;
  return 2;
}
#define snprintf vp_snprintf

#include SHA256_C

void h_bytes(void) {
  uint8_t b[4], sb[4];
  exp_buf = b; exp_buf_len = nondet_size();
  exp_salt = nondet_u8() & 1 ? sb : NULL; exp_salt_len = nondet_size();
  const char *r = sha256_bytes(exp_buf, exp_buf_len, exp_salt, exp_salt_len);
  __CPROVER_assert(seq == 4, "finished");
  const char *hx = "0123456789abcdef";
  for (int i = 0; i < 32; i++)
    __CPROVER_assert(r[2 * i] == hx[made[i] >> 4] && r[2 * i + 1] == hx[made[i] & 15], "hex digits");
  __CPROVER_assert(r[64] == 0, "NUL");
}
