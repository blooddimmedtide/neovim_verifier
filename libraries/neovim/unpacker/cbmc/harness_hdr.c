// CBMC harness for unpacker_parse_header against the msgpack-rpc header format
// (github.com/msgpack-rpc/msgpack-rpc/blob/master/spec.md):
//   request      [0, msgid, method, params]   (4 elements)
//   response     [1, msgid, error, result]    (4 elements)
//   notification [2, method, params]          (3 elements)
// msgid is a 32-bit unsigned integer, type an integer 0..2, method a string (Neovim also
// accepts bin and limits names to 100 bytes; that limit is Neovim's own, stated here).
// The header is the array head, type, msgid and method; params/result stay unread.
#include INIT_C
#include "spec.h"
#include <assert.h>
#include <stdlib.h>
size_t nondet_size(void);
int nondet_int(void);
MsgpackRpcRequestHandler nondet_handler(void);

static int calls; static const char *c_name; static size_t c_len; static MsgpackRpcRequestHandler c_ret;
MsgpackRpcRequestHandler msgpack_rpc_get_handler_for(const char *name, size_t name_len, Error *error)
{
  calls++; c_name = name; c_len = name_len;
  if (nondet_int()) { error->type = kErrorTypeException; }   // may report "Invalid method"
  c_ret = nondet_handler();
  return c_ret;
}
static int set_err;
void api_set_error(Error *err, ErrorType errType, const char *format, ...)
{
  set_err++; err->type = errType;
}

enum { R_OK, R_EOF, R_ERR };
// Reference: parse an integer element that must be an unsigned value below 2^limbits.
static int ref_uint(const unsigned char *b, size_t n, size_t *at, uint64_t *v, int bits)
{
  size_t hdr; int64_t val; int wrapped;
  if (*at >= n) return R_EOF;
  unsigned t = b[*at];
  int is_int = t <= 0x7f || t >= 0xe0 || (t >= 0xcc && t <= 0xd3);
  if (!is_int) return R_ERR;
  if (!ref_int(b + *at, n - *at, &hdr, &val, &wrapped)) return R_EOF;  // int, but cut off
  uint64_t u = (uint64_t)val;
  if (!wrapped && val < 0) return R_ERR;                       // negative
  if (bits < 64 && u >> bits) return R_ERR;                     // too large
  *at += hdr; *v = u; return R_OK;
}

static int ref_header(const unsigned char *b, size_t n, uint64_t *type, uint64_t *id,
                      size_t *name_at, size_t *name_len, size_t *used)
{
  size_t at = 0, hdr; uint64_t cnt;
  if (n == 0) return R_EOF;
  unsigned t = b[0];
  if (!((t >= 0x90 && t <= 0x9f) || t == 0xdc || t == 0xdd)) return R_ERR;
  if (!ref_arrhdr(b, n, &hdr, &cnt)) return R_EOF;
  if (cnt != 3 && cnt != 4) return R_ERR;
  at = hdr;
  int r = ref_uint(b, n, &at, type, 32);   // reference decision: type must fit the uint32 Neovim keeps
  if (r) return r;
  if (cnt == 3 ? *type != 2 : *type > 1) return R_ERR;
  *id = 0;
  if (*type != 2) { r = ref_uint(b, n, &at, id, 32); if (r) return r; }
  *name_len = 0; *name_at = at;
  if (*type != 1) {
    if (at >= n) return R_EOF;
    unsigned s = b[at];
    int is_str = (s >= 0xa0 && s <= 0xbf) || (s >= 0xd9 && s <= 0xdb) || (s >= 0xc4 && s <= 0xc6);
    if (!is_str) return R_ERR;
    uint64_t len;
    if (!ref_strhdr(b + at, n - at, &hdr, &len)) return R_EOF;
    if (len > 100) return R_ERR;
    at += hdr;
    if (n - at < len) return R_EOF;
    *name_at = at; *name_len = (size_t)len; at += (size_t)len;
  }
  *used = at; return R_OK;
}

Unpacker nondet_unpacker(void);
void h_unpacker_parse_header(void)
{
  size_t n = nondet_size();
  __CPROVER_assume(n < ((size_t)1 << 32));   // mpack_read's chunk length is uint32 (findings/mpack-chunk-over-4gib.md)
  const char *b = malloc(n);
  Unpacker p = nondet_unpacker(), before = p;
  // entry state: as left by unpacker_init or by a completed message: no error, empty reader
  __CPROVER_assume(p.unpack_error.type == kErrorTypeNone);
  __CPROVER_assume(p.reader.ppos == 0 && p.reader.plen == 0 && p.reader.passthrough == 0);
  p.read_ptr = b; p.read_size = n; before = p;
  bool ok = unpacker_parse_header(&p);
  uint64_t type, id; size_t na, nl, used;
  int r = ref_header((const unsigned char *)b, n, &type, &id, &na, &nl, &used);
  if (r == R_OK) {
    assert(ok);
    assert(p.type == (MessageType)type && p.request_id == id);
    assert(p.read_ptr == b + used && p.read_size == n - used);
    assert(p.state == before.state);
    if (type != 1) {
      assert(calls == 1 && c_len == nl && p.method_name_len == nl);
      assert(nl == 0 || c_name == b + na);
      assert(p.handler.fn == c_ret.fn);
    } else {
      assert(calls == 0);
    }
  } else if (r == R_EOF) {   // wait for more data: nothing consumed, reader reset, no error
    assert(!ok);
    assert(p.read_ptr == b && p.read_size == n && p.state == before.state);
    assert(p.reader.ppos == 0 && p.reader.plen == 0 && p.reader.passthrough == 0);
    assert(set_err == 0);
  } else {                   // malformed: closed with an error
    assert(!ok);
    assert(p.state == -1 && set_err == 1 && p.unpack_error.type == kErrorTypeValidation);
    assert(p.read_ptr == b && p.read_size == n);
  }
}
