// CBMC proofs of sha256_update / sha256_finish as streams of 64-byte blocks.
// sha256_process is replaced (goto-instrument --replace-calls) by rec_process, which checks
// that every block it is given is the next 64 bytes of the stream "bytes already buffered,
// then the new input" (one nondeterministic byte position per call, so every position is
// covered), and that the context is the caller's. h_process + check_structure.py prove the
// real sha256_process is one FIPS compression; together the digest is FIPS SHA-256.
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "nvim/sha256.h"

size_t nondet_size(void);
static size_t rec_calls;            // blocks processed so far in this call
static const uint8_t *rec_in0;      // the input of this call
static size_t rec_len0;
static size_t rec_left0;            // bytes already buffered when the call started
static uint8_t rec_buf0[64];        // the buffer when the call started
static context_sha256_T *rec_ctx;
static size_t rec_b;                // the byte position checked in every block

static uint8_t stream_byte(size_t s) { return s < rec_left0 ? rec_buf0[s] : rec_in0[s - rec_left0]; }

void rec_process(context_sha256_T *ctx, const uint8_t data[SHA256_BUFFER_SIZE]) {
  __CPROVER_assert(ctx == rec_ctx, "process gets the caller's context");
  __CPROVER_assert((rec_calls + 1) * 64 <= rec_left0 + rec_len0, "only whole blocks of the stream");
#ifndef NO_BLOCK_CHECK
  __CPROVER_assert(data[rec_b] == stream_byte(rec_calls * 64 + rec_b), "block = next 64 stream bytes");
#endif
  ctx->state[0] = ctx->state[0] * 31 + 7;   // some change, so later code cannot rely on the old state
  rec_calls++;
}

// Loop invariant of sha256_update's block loop (inserted by build.py).
#define REC_F (rec_left0 != 0 && rec_len0 >= 64 - rec_left0)        // the buffer was completed first
#define REC_USED (REC_F ? 64 - rec_left0 : 0)
#define LOOP_INV (rec_calls >= (size_t)REC_F && rec_calls <= (rec_left0 + rec_len0) / 64 \
                  && input == rec_in0 + REC_USED + 64 * (rec_calls - REC_F) \
                  && length == rec_len0 - REC_USED - 64 * (rec_calls - REC_F) \
                  && left == (REC_F ? 0 : rec_left0) && ctx == rec_ctx)

#include SHA256_X_C

void h_update(void) {
  context_sha256_T ctx_obj;
  context_sha256_T *ctx = &ctx_obj;
  size_t len = nondet_size();
  __CPROVER_assume(len <= SIZE_MAX - 64);
#ifndef SHA256_FIXED
  __CPROVER_assume(len <= 0xFFFFFFFF);   // upstream is wrong past this (findings/sha256-length-over-8gib.md)
#endif
  uint8_t *in = malloc(len);
  __CPROVER_assume(in != NULL);   // the caller's input exists (malloc success)
  rec_calls = 0; rec_in0 = in; rec_len0 = len; rec_ctx = ctx;
  rec_left0 = ctx->total[0] & 63;
  memcpy(rec_buf0, ctx->buffer, 64);
  rec_b = nondet_size();
  __CPROVER_assume(rec_b < 64);
  uint64_t T0 = (uint64_t)ctx->total[1] << 32 | ctx->total[0];

  sha256_update(ctx, in, len);

  __CPROVER_assert(rec_calls == (rec_left0 + len) / 64, "every complete block processed");
  uint64_t T1 = (uint64_t)ctx->total[1] << 32 | ctx->total[0];
  __CPROVER_assert(T1 == T0 + len, "byte count");
#ifndef NO_TAIL_CHECK
  size_t i = nondet_size();
  if (i < (rec_left0 + len) % 64)
    __CPROVER_assert(ctx->buffer[i] == stream_byte(rec_calls * 64 + i), "the rest is buffered");
#endif
}
