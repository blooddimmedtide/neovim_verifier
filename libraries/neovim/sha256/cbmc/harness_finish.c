// CBMC proof of sha256_finish: from any context (any byte count T, any buffered tail of
// T mod 64 bytes), it processes the tail followed by FIPS 180-4's padding (0x80, zeros,
// the 64-bit big-endian bit length 8T) as whole blocks, then writes the state big-endian.
// sha256_process is replaced by rec_process (goto-instrument --replace-calls), which checks
// each block against that stream at one nondeterministic byte position.
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include "nvim/sha256.h"

size_t nondet_size(void);
static size_t rec_calls, rec_left0, rec_padlen, rec_b;
static uint64_t rec_bits;
static uint8_t rec_buf0[64];
static context_sha256_T *rec_ctx;

static uint8_t padded_byte(size_t s) {
  if (s < rec_left0) return rec_buf0[s];
  if (s == rec_left0) return 0x80;
  if (s < rec_padlen - 8) return 0;
  return (uint8_t)(rec_bits >> (8 * (rec_padlen - 1 - s)));   // big-endian bit length
}

void rec_process(context_sha256_T *ctx, const uint8_t data[SHA256_BUFFER_SIZE]) {
  __CPROVER_assert(ctx == rec_ctx, "process gets the caller's context");
  __CPROVER_assert((rec_calls + 1) * 64 <= rec_padlen, "only whole blocks of the padded stream");
  __CPROVER_assert(data[rec_b] == padded_byte(rec_calls * 64 + rec_b), "block = padded stream");
  for (int i = 0; i < 8; i++) ctx->state[i] = ctx->state[i] * 31 + (uint32_t)rec_calls;  // some change
  rec_calls++;
}

#include SHA256_C

void h_finish(void) {
  context_sha256_T ctx_obj, *ctx = &ctx_obj;
  rec_ctx = ctx; rec_calls = 0;
  rec_left0 = ctx->total[0] & 63;
  memcpy(rec_buf0, ctx->buffer, 64);
  rec_bits = ((uint64_t)ctx->total[1] << 32 | ctx->total[0]) << 3;   // 8T mod 2^64
  rec_padlen = rec_left0 < 56 ? 64 : 128;
  rec_b = nondet_size();
  __CPROVER_assume(rec_b < 64);
  uint8_t digest[SHA256_SUM_SIZE];
  sha256_finish(ctx, digest);
  __CPROVER_assert(rec_calls == rec_padlen / 64, "all padded blocks processed");
  for (int i = 0; i < 32; i++)
    __CPROVER_assert(digest[i] == (uint8_t)(ctx->state[i / 4] >> (24 - 8 * (i % 4))), "digest = state, big-endian");
}
