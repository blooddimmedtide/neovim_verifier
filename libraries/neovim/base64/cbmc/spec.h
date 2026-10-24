// Reference model of RFC 4648 Base64 (standard alphabet, with padding),
// written byte by byte for clarity rather than speed.
#pragma once
#include <stddef.h>
#include <stdint.h>
static const char ref_alpha[] =
  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
static char ref_enc_char(size_t i, const uint8_t *s, size_t n) {
  // Output char i of encode(s): group g = i/4, position k = i%4.
  size_t g = i / 4, k = i % 4, b = g * 3;
  uint32_t w = 0;
  for (size_t j = 0; j < 3; j++) w = (w << 8) | (b + j < n ? s[b + j] : 0);
  size_t present = n - b;            // bytes present in this group (>=1)
  if (present > 3) present = 3;
  if (k > present) return '=';       // 1 byte -> 2 chars, 2 bytes -> 3 chars
  return ref_alpha[(w >> (18 - 6 * k)) & 0x3F];
}
