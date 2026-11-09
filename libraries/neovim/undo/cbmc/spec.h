// Independent reference for the undo-file byte format, from the documented meaning
// ("number, most significant byte first, in len bytes"; get4c: "-1 when encountering EOF").
// It uses integer arithmetic only (no shifts), so it shares no code with what it checks.
#include <stdint.h>
typedef unsigned __int128 u128;
typedef __int128 i128;

// Value of in[off .. off+n) read as a big-endian unsigned number.
static u128 be_value(const uint8_t *in, size_t off, size_t n) {
  u128 v = 0;
  for (size_t k = 0; k < n; k++) v = v * 256 + in[off + k];
  return v;
}
// 256^n as an exact integer (n <= 8).
static u128 pow256(size_t n) { u128 p = 1; for (size_t k = 0; k < n; k++) p *= 256; return p; }
// Two's complement reading of an n-byte unsigned value (the stored bits as a signed number).
static i128 as_signed(u128 v, size_t n) {
  u128 half = pow256(n) / 2;
  return v < half ? (i128)v : (i128)v - (i128)pow256(n);
}
// What get4c / undo_read_4c returns for a stream holding in[off .. len).
static i128 spec_4c(const uint8_t *in, size_t len, size_t off) {
  if (len < off + 4) return -1;
  return as_signed(be_value(in, off, 4), 4);
}
