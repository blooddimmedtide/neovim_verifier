// SHA-256 written from FIPS 180-4 (sections 4.1.2, 4.2.2, 5.3.3, 6.2.2), not from Neovim's code.
#pragma once
#include <stdint.h>

static uint32_t spec_rotr(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }
static uint32_t spec_ch(uint32_t x, uint32_t y, uint32_t z) { return (x & y) ^ (~x & z); }
static uint32_t spec_maj(uint32_t x, uint32_t y, uint32_t z) { return (x & y) ^ (x & z) ^ (y & z); }
static uint32_t spec_bsig0(uint32_t x) { return spec_rotr(x, 2) ^ spec_rotr(x, 13) ^ spec_rotr(x, 22); }
static uint32_t spec_bsig1(uint32_t x) { return spec_rotr(x, 6) ^ spec_rotr(x, 11) ^ spec_rotr(x, 25); }
static uint32_t spec_ssig0(uint32_t x) { return spec_rotr(x, 7) ^ spec_rotr(x, 18) ^ (x >> 3); }
static uint32_t spec_ssig1(uint32_t x) { return spec_rotr(x, 17) ^ spec_rotr(x, 19) ^ (x >> 10); }

static const uint32_t SPEC_K[64] = {
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
};
static const uint32_t SPEC_H0[8] = {
  0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
};

// Equivalent forms of Ch and Maj (the forms many implementations use). h_forms proves them
// equal to the FIPS definitions above for all inputs; spec_compress uses these forms so that
// the solver can match the code's formula term by term.
static uint32_t spec_ch_alt(uint32_t x, uint32_t y, uint32_t z) { return z ^ (x & (y ^ z)); }
static uint32_t spec_maj_alt(uint32_t x, uint32_t y, uint32_t z) { return (x & y) | (z & (x | y)); }

// One SHA-256 compression (FIPS 180-4 6.2.2 steps 1-4) of block m into H.
static void spec_compress(uint32_t H[8], const uint8_t m[64]) {
  uint32_t W[64];
  for (int t = 0; t < 16; t++)
    W[t] = (uint32_t)m[4 * t] << 24 | (uint32_t)m[4 * t + 1] << 16 | (uint32_t)m[4 * t + 2] << 8 | m[4 * t + 3];
  for (int t = 16; t < 64; t++)
    W[t] = spec_ssig1(W[t - 2]) + W[t - 7] + spec_ssig0(W[t - 15]) + W[t - 16];
  uint32_t a = H[0], b = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
  for (int t = 0; t < 64; t++) {
    uint32_t T1 = h + spec_bsig1(e) + spec_ch_alt(e, f, g) + SPEC_K[t] + W[t];
    uint32_t T2 = spec_bsig0(a) + spec_maj_alt(a, b, c);
    h = g; g = f; f = e; e = d + T1; d = c; c = b; b = a; a = T1 + T2;
  }
  H[0] += a; H[1] += b; H[2] += c; H[3] += d; H[4] += e; H[5] += f; H[6] += g; H[7] += h;
}
