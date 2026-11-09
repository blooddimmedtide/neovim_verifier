// Independent reference for the msgpack token readers of src/nvim/msgpack_rpc/unpacker.c,
// written from the MessagePack specification (github.com/msgpack/msgpack/blob/master/spec.md),
// not from the code. All multi-byte fields are big-endian.
#include <stdint.h>
#include <stddef.h>

static uint64_t ref_be(const unsigned char *p, int n)
{
  uint64_t v = 0;
  for (int i = 0; i < n; i++) {
    v = (v << 8) | p[i];
  }
  return v;
}

// str or bin header: 1 when b[0..n) starts with one, with header length and payload length.
// fixstr 101xxxxx, str8 d9, str16 da, str32 db, bin8 c4, bin16 c5, bin32 c6.
static int ref_strhdr(const unsigned char *b, size_t n, size_t *hdr, uint64_t *len)
{
  if (n < 1) return 0;
  unsigned t = b[0]; int w;
  if (t >= 0xa0 && t <= 0xbf) { *hdr = 1; *len = t & 0x1f; return 1; }
  if (t == 0xd9 || t == 0xc4) w = 1;
  else if (t == 0xda || t == 0xc5) w = 2;
  else if (t == 0xdb || t == 0xc6) w = 4;
  else return 0;
  if (n < (size_t)(1 + w)) return 0;
  *hdr = 1 + (size_t)w; *len = ref_be(b + 1, w); return 1;
}

// array header: fixarray 1001xxxx, array16 dc, array32 dd.
static int ref_arrhdr(const unsigned char *b, size_t n, size_t *hdr, uint64_t *len)
{
  if (n < 1) return 0;
  unsigned t = b[0]; int w;
  if (t >= 0x90 && t <= 0x9f) { *hdr = 1; *len = t & 0x0f; return 1; }
  if (t == 0xdc) w = 2; else if (t == 0xdd) w = 4; else return 0;
  if (n < (size_t)(1 + w)) return 0;
  *hdr = 1 + (size_t)w; *len = ref_be(b + 1, w); return 1;
}

// integer: positive fixint 0xxxxxxx, negative fixint 111xxxxx, uint8..64 cc..cf, int8..64 d0..d3.
// Value as a 64-bit two's complement word. Reference decision: a uint64 of 2^63 or more has no
// Integer (int64_t) value; the reference gives its two's complement reinterpretation (value - 2^64)
// and *wrapped is set, so the claim can say exactly what callers see (see CLAIM.md, reference decision).
static int ref_int(const unsigned char *b, size_t n, size_t *hdr, int64_t *val, int *wrapped)
{
  *wrapped = 0;
  if (n < 1) return 0;
  unsigned t = b[0];
  if (t <= 0x7f) { *hdr = 1; *val = (int64_t)t; return 1; }
  if (t >= 0xe0) { *hdr = 1; *val = (int64_t)t - 256; return 1; }
  int w, sgn;
  if (t >= 0xcc && t <= 0xcf) { w = 1 << (t - 0xcc); sgn = 0; }
  else if (t >= 0xd0 && t <= 0xd3) { w = 1 << (t - 0xd0); sgn = 1; }
  else return 0;
  if (n < (size_t)(1 + w)) return 0;
  uint64_t u = ref_be(b + 1, w);
  *hdr = 1 + (size_t)w;
  if (!sgn) {
    if (u >= ((uint64_t)1 << 63)) { *wrapped = 1; *val = -(int64_t)(UINT64_MAX - u) - 1; }
    else *val = (int64_t)u;
    return 1;
  }
  // signed: two's complement of w bytes
  int bits = 8 * w;
  if (bits == 64) {
    *val = (u >> 63) ? -(int64_t)(UINT64_MAX - u) - 1 : (int64_t)u;
  } else {
    int64_t s = (int64_t)u;
    if (u >> (bits - 1)) s -= (int64_t)1 << bits;
    *val = s;
  }
  return 1;
}
