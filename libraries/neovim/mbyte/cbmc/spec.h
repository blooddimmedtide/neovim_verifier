// Reference meaning of UTF-8, written from RFC 3629 and the original 1-6 byte
// form of RFC 2279 (which Neovim accepts), not from Neovim's code or tables.
//
// An n-byte sequence (n = 1..6) is a lead byte with n leading 1 bits followed
// by a 0 (for n = 1: a top bit of 0), then n-1 continuation bytes 10xxxxxx.
// It carries 7 value bits for n = 1, and (7 - n) + 6 (n - 1) = 5n + 1 for n >= 2.
#include <stdint.h>
#include <stdbool.h>

// Number of leading 1 bits of a byte (0..8).
static int spec_leading_ones(uint8_t b) {
  int k = 0;
  while (k < 8 && (b & (0x80u >> k))) k++;
  return k;
}

// Length announced by a lead byte. A byte that cannot start a sequence
// (a continuation byte 10xxxxxx, or 0xFE / 0xFF with 7 or 8 leading ones)
// counts as one byte.
static int spec_lead_len(uint8_t b) {
  int k = spec_leading_ones(b);
  if (k == 0) return 1;
  if (k == 1 || k >= 7) return 1;
  return k;
}

static bool spec_is_cont(uint8_t b) { return (b >> 6) == 2; }

// Value bits of an n-byte sequence.
static int spec_bits(int n) { return n == 1 ? 7 : 5 * n + 1; }

// Value of the n-byte sequence at b (lead payload, then 6 bits per byte).
static uint32_t spec_value(const uint8_t *b, int n) {
  uint32_t v = n == 1 ? b[0] : (uint32_t)(b[0] & (0xFFu >> (n + 1)));
  for (int k = 1; k < n; k++) v = v * 64 + (b[k] & 0x3Fu);
  return v;
}

// Shortest encoding length of a value 0 <= c < 2^31: the smallest n whose
// value bits hold c.
static int spec_enc_len(int64_t c) {
  for (int n = 1; n <= 6; n++)
    if (c < ((int64_t)1 << spec_bits(n))) return n;
  return -1;  // unreachable for c < 2^31
}

// Reference for utf_ptr2len: 0 for "", the announced length when all its
// continuation bytes are there, 1 otherwise.
static int ref_ptr2len(const uint8_t *p) {
  if (p[0] == 0) return 0;
  int L = spec_lead_len(p[0]);
  for (int k = 1; k < L; k++) if (!spec_is_cont(p[k])) return 1;
  return L;
}

// Reference for utf_ptr2char: the value of a complete sequence, else the
// first byte's value.
static int ref_ptr2char(const uint8_t *p) {
  int L = spec_lead_len(p[0]);
  if (p[0] < 0x80 || L < 2) return p[0];
  for (int k = 1; k < L; k++) if (!spec_is_cont(p[k])) return p[0];
  return (int)spec_value(p, L);
}

// Reference for utf_ptr2len_len(p, size): 1 when the lead byte is a 1-byte
// sequence (also NUL); otherwise the announced length L if the continuation
// bytes that fit in size are all there (the result is then > size when the
// sequence is cut off), and 1 if one of them is wrong.
static int ref_ptr2len_len(const uint8_t *p, int size) {
  int L = spec_lead_len(p[0]);
  if (L == 1) return 1;
  int m = L < size ? L : size;
  for (int k = 1; k < m; k++) if (!spec_is_cont(p[k])) return 1;
  return L;
}
