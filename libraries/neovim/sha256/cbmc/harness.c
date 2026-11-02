// CBMC proofs for src/nvim/sha256.c (included unchanged).
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include "spec.h"
#include SHA256_C

// sha256_start sets the FIPS initial hash value and a zero length.
void h_start(void) {
  context_sha256_T ctx;
  sha256_start(&ctx);
  __CPROVER_assert(ctx.total[0] == 0 && ctx.total[1] == 0, "length 0");
  for (int i = 0; i < 8; i++) __CPROVER_assert(ctx.state[i] == SPEC_H0[i], "H(0)");
}

// sha256_process is one FIPS compression, for every state and block.
void h_process(void) {
  context_sha256_T ctx;
  uint8_t data[64];
  uint32_t H[8];
  for (int i = 0; i < 8; i++) H[i] = ctx.state[i];
  sha256_process(&ctx, data);
  spec_compress(H, data);
  for (int i = 0; i < 8; i++) __CPROVER_assert(ctx.state[i] == H[i], "compression");
}

// The alternative Ch/Maj forms used by spec_compress equal FIPS 180-4's, for all inputs.
void h_forms(void) {
  uint32_t x, y, z;
  __CPROVER_assert(spec_ch_alt(x, y, z) == spec_ch(x, y, z), "Ch");
  __CPROVER_assert(spec_maj_alt(x, y, z) == spec_maj(x, y, z), "Maj");
}

// ---- Compositional proof of sha256_process (the direct equivalence is too big for SAT) ----
// The helper macros (defined in sha256.c's body, still visible here) equal FIPS 180-4's
// functions for all inputs.
void h_prims(void) {
  uint32_t x, y, z;
  __CPROVER_assert(S0(x) == spec_ssig0(x), "S0 = sigma0");
  __CPROVER_assert(S1(x) == spec_ssig1(x), "S1 = sigma1");
  __CPROVER_assert(S2(x) == spec_bsig0(x), "S2 = Sigma0");
  __CPROVER_assert(S3(x) == spec_bsig1(x), "S3 = Sigma1");
  __CPROVER_assert(F0(x, y, z) == spec_maj(x, y, z), "F0 = Maj");
  __CPROVER_assert(F1(x, y, z) == spec_ch(x, y, z), "F1 = Ch");
}

// One P(a, ..., h, x, K) step is one FIPS round, with the working variables renamed:
// it sets d to d + T1 and h to T1 + T2 and changes nothing else. Calling it with the
// names rotated by one each round (checked by check_structure.py) gives FIPS's shift.
void h_round(void) {
  uint32_t temp1, temp2;
  uint32_t A, B, C, D, E, F, G, H, X, K;
  uint32_t a = A, b = B, c = C, d = D, e = E, f = F, g = G, h = H;
  P(A, B, C, D, E, F, G, H, X, K);
  uint32_t T1 = h + spec_bsig1(e) + spec_ch(e, f, g) + K + X;
  uint32_t T2 = spec_bsig0(a) + spec_maj(a, b, c);
  __CPROVER_assert(D == d + T1 && H == T1 + T2, "round");
  __CPROVER_assert(A == a && B == b && C == c && E == e && F == f && G == g, "others kept");
}

// R(t) computes FIPS's message schedule word t from the earlier words, for every t in 16..63.
void h_sched(void) {
  uint32_t W[64], V[64];
  int t;
  __CPROVER_assume(16 <= t && t < 64);
  for (int i = 0; i < 64; i++) V[i] = W[i];
  uint32_t r = R(t);
  uint32_t want = spec_ssig1(V[t - 2]) + V[t - 7] + spec_ssig0(V[t - 15]) + V[t - 16];
  __CPROVER_assert(r == want && W[t] == want, "schedule");
  for (int i = 0; i < 64; i++) if (i != t) __CPROVER_assert(W[i] == V[i], "only W[t] written");
}

// GET_UINT32 / PUT_UINT32 are big-endian loads and stores.
void h_endian(void) {
  uint8_t b[8]; uint32_t n, v; int i;
  __CPROVER_assume(0 <= i && i <= 4);
  GET_UINT32(n, b, i);
  __CPROVER_assert(n == ((uint32_t)b[i] << 24 | (uint32_t)b[i + 1] << 16 | (uint32_t)b[i + 2] << 8 | b[i + 3]), "get");
  uint8_t c[8], d[8];
  for (int k = 0; k < 8; k++) d[k] = c[k];
  PUT_UINT32(v, c, i);
  __CPROVER_assert(c[i] == (uint8_t)(v >> 24) && c[i + 1] == (uint8_t)(v >> 16) && c[i + 2] == (uint8_t)(v >> 8) && c[i + 3] == (uint8_t)v, "put");
  for (int k = 0; k < 8; k++) if (k < i || k > i + 3) __CPROVER_assert(c[k] == d[k], "put writes 4 bytes");
}
