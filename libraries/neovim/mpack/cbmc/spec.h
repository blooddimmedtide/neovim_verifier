// Reference meaning of MessagePack tokens, written from the MessagePack
// specification (https://github.com/msgpack/msgpack/blob/master/spec.md),
// not from mpack_core.c. A "token" is one header: a scalar with its value, or
// the header of a str/bin/ext/array/map with its length (the payload bytes of
// str/bin/ext follow as separate CHUNK tokens).
//
// Where the spec leaves a choice to the library, the reference states
// libmpack's documented choice (mpack_core.h):
//  - integers keep their raw big-endian bits in value.hi:value.lo (not sign
//    extended); an int 8/16/32/64 whose sign bit is clear is reported as UINT,
//    and a negative fixint as SINT with lo = the raw byte;
//  - the ext type byte is reported as 0..255 (the spec's int8 read as unsigned);
//  - `length` is the payload size in bytes for ints, floats and bool (1), 0 for nil.
#include <stdint.h>
#include <stddef.h>
#include <string.h>

enum { R_OK = 0, R_EOF = 1, R_ERROR = 2 };
enum { T_NIL = 1, T_BOOL, T_UINT, T_SINT, T_FLOAT, T_CHUNK, T_ARRAY, T_MAP, T_BIN, T_STR, T_EXT };

typedef struct {
  int type;
  uint32_t length;
  uint32_t lo, hi;   // value types
  int ext_type;      // EXT
} ref_tok;

static uint32_t be_n(const uint8_t *p, int k) {
  uint32_t v = 0;
  for (int i = 0; i < k; i++) v = (v << 8) | p[i];
  return v;
}

// Header layout of a first byte, from the spec's format table.
//   kind 0: fixed value in the first byte     kind 1: value of `size` bytes follows
//   kind 2: length of `size` bytes follows    kind 3: length `size` bytes, then ext type byte
//   kind 4: fixext: ext type byte follows, payload `size`      kind -1: never used (0xc1)
typedef struct { int kind, type, size; } layout;

static layout ref_layout(uint8_t t) {
  if (t <= 0x7f) return (layout){0, T_UINT, 0};    // positive fixint 0xxxxxxx
  if (t <= 0x8f) return (layout){0, T_MAP, 0};     // fixmap 1000xxxx
  if (t <= 0x9f) return (layout){0, T_ARRAY, 0};   // fixarray 1001xxxx
  if (t <= 0xbf) return (layout){0, T_STR, 0};     // fixstr 101xxxxx
  if (t >= 0xe0) return (layout){0, T_SINT, 0};    // negative fixint 111xxxxx
  switch (t) {
    case 0xc0: return (layout){0, T_NIL, 0};
    case 0xc2: case 0xc3: return (layout){0, T_BOOL, 0};
    case 0xc4: return (layout){2, T_BIN, 1};
    case 0xc5: return (layout){2, T_BIN, 2};
    case 0xc6: return (layout){2, T_BIN, 4};
    case 0xc7: return (layout){3, T_EXT, 1};
    case 0xc8: return (layout){3, T_EXT, 2};
    case 0xc9: return (layout){3, T_EXT, 4};
    case 0xca: return (layout){1, T_FLOAT, 4};
    case 0xcb: return (layout){1, T_FLOAT, 8};
    case 0xcc: return (layout){1, T_UINT, 1};
    case 0xcd: return (layout){1, T_UINT, 2};
    case 0xce: return (layout){1, T_UINT, 4};
    case 0xcf: return (layout){1, T_UINT, 8};
    case 0xd0: return (layout){1, T_SINT, 1};
    case 0xd1: return (layout){1, T_SINT, 2};
    case 0xd2: return (layout){1, T_SINT, 4};
    case 0xd3: return (layout){1, T_SINT, 8};
    case 0xd4: return (layout){4, T_EXT, 1};
    case 0xd5: return (layout){4, T_EXT, 2};
    case 0xd6: return (layout){4, T_EXT, 4};
    case 0xd7: return (layout){4, T_EXT, 8};
    case 0xd8: return (layout){4, T_EXT, 16};
    case 0xd9: return (layout){2, T_STR, 1};
    case 0xda: return (layout){2, T_STR, 2};
    case 0xdb: return (layout){2, T_STR, 4};
    case 0xdc: return (layout){2, T_ARRAY, 2};
    case 0xdd: return (layout){2, T_ARRAY, 4};
    case 0xde: return (layout){2, T_MAP, 2};
    case 0xdf: return (layout){2, T_MAP, 4};
    default: return (layout){-1, 0, 0};             // 0xc1: never used
  }
}

// Total header size in bytes (first byte included).
static size_t ref_hdr(uint8_t t) {
  layout l = ref_layout(t);
  switch (l.kind) {
    case 0: return 1;
    case 1: case 2: return 1 + (size_t)l.size;
    case 3: return 2 + (size_t)l.size;
    case 4: return 2;
    default: return 1;
  }
}

// Decode the token at b[0..n-1]. OK: *r is the token and *used its header
// size. EOF: n is shorter than the header and *need is the header size minus 1
// (what libmpack reports in tok->length). ERROR: 0xc1.
static int ref_decode(const uint8_t *b, size_t n, ref_tok *r, size_t *used, uint32_t *need) {
  memset(r, 0, sizeof *r);
  if (n == 0) return R_EOF;
  uint8_t t = b[0];
  layout l = ref_layout(t);
  if (l.kind < 0) return R_ERROR;
  size_t h = ref_hdr(t);
  if (n < h) { *need = (uint32_t)(h - 1); return R_EOF; }
  *used = h;
  r->type = l.type;
  switch (l.kind) {
    case 0:
      if (l.type == T_UINT || l.type == T_SINT) { r->length = 1; r->lo = t; }
      else if (l.type == T_BOOL) { r->length = 1; r->lo = t & 1; }
      else if (l.type == T_MAP || l.type == T_ARRAY) r->length = t & 0x0f;
      else if (l.type == T_STR) r->length = t & 0x1f;
      break;
    case 1:
      r->length = (uint32_t)l.size;
      if (l.size == 8) { r->hi = be_n(b + 1, 4); r->lo = be_n(b + 5, 4); }
      else r->lo = be_n(b + 1, l.size);
      if (l.type == T_SINT && !(b[1] & 0x80)) r->type = T_UINT;   // sign bit clear
      break;
    case 2: r->length = be_n(b + 1, l.size); break;
    case 3: r->length = be_n(b + 1, l.size); r->ext_type = b[1 + l.size]; break;
    case 4: r->length = (uint32_t)l.size; r->ext_type = b[1]; break;
  }
  return R_OK;
}

// Shortest encoding of a token, as the spec asks writers to use. Returns the
// byte count. For SINT the value is the 64-bit two's complement hi:lo, < 0.
static int ref_encode(const ref_tok *k, uint8_t *o) {
  uint64_t u = ((uint64_t)k->hi << 32) | k->lo;
  int64_t s = (int64_t)u;
  uint32_t n = k->length;
#define PUT(v, bytes) do { for (int i_ = (bytes) - 1; i_ >= 0; i_--) o[w++] = (uint8_t)((uint64_t)(v) >> (8 * i_)); } while (0)
  int w = 0;
  switch (k->type) {
    case T_NIL: o[w++] = 0xc0; break;
    case T_BOOL: o[w++] = k->lo ? 0xc3 : 0xc2; break;
    case T_UINT:
      if (u <= 0x7f) PUT(u, 1);
      else if (u <= 0xff) { o[w++] = 0xcc; PUT(u, 1); }
      else if (u <= 0xffff) { o[w++] = 0xcd; PUT(u, 2); }
      else if (u <= 0xffffffffu) { o[w++] = 0xce; PUT(u, 4); }
      else { o[w++] = 0xcf; PUT(u, 8); }
      break;
    case T_SINT:
      if (s >= -32) PUT(s, 1);
      else if (s >= -128) { o[w++] = 0xd0; PUT(s, 1); }
      else if (s >= -32768) { o[w++] = 0xd1; PUT(s, 2); }
      else if (s >= INT32_MIN) { o[w++] = 0xd2; PUT(s, 4); }
      else { o[w++] = 0xd3; PUT(s, 8); }
      break;
    case T_FLOAT:
      if (n == 4) { o[w++] = 0xca; PUT(k->lo, 4); }
      else { o[w++] = 0xcb; PUT(u, 8); }
      break;
    case T_STR:
      if (n <= 31) o[w++] = (uint8_t)(0xa0 + n);
      else if (n <= 0xff) { o[w++] = 0xd9; PUT(n, 1); }
      else if (n <= 0xffff) { o[w++] = 0xda; PUT(n, 2); }
      else { o[w++] = 0xdb; PUT(n, 4); }
      break;
    case T_BIN:
      if (n <= 0xff) { o[w++] = 0xc4; PUT(n, 1); }
      else if (n <= 0xffff) { o[w++] = 0xc5; PUT(n, 2); }
      else { o[w++] = 0xc6; PUT(n, 4); }
      break;
    case T_EXT:
      if (n == 1) o[w++] = 0xd4; else if (n == 2) o[w++] = 0xd5; else if (n == 4) o[w++] = 0xd6;
      else if (n == 8) o[w++] = 0xd7; else if (n == 16) o[w++] = 0xd8;
      else if (n <= 0xff) { o[w++] = 0xc7; PUT(n, 1); }
      else if (n <= 0xffff) { o[w++] = 0xc8; PUT(n, 2); }
      else { o[w++] = 0xc9; PUT(n, 4); }
      o[w++] = (uint8_t)k->ext_type;
      break;
    case T_ARRAY:
      if (n <= 15) o[w++] = (uint8_t)(0x90 + n);
      else if (n <= 0xffff) { o[w++] = 0xdc; PUT(n, 2); }
      else { o[w++] = 0xdd; PUT(n, 4); }
      break;
    case T_MAP:
      if (n <= 15) o[w++] = (uint8_t)(0x80 + n);
      else if (n <= 0xffff) { o[w++] = 0xde; PUT(n, 2); }
      else { o[w++] = 0xdf; PUT(n, 4); }
      break;
  }
#undef PUT
  return w;
}
