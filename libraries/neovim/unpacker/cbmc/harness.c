// CBMC harnesses: the real unpacker.c functions (verbatim, with the real mpack reader)
// against spec.h, for every byte content and every buffer length below 2^48.
#include UNPACKER_C
#include "spec.h"
#include <stdlib.h>
#include <assert.h>
size_t nondet_size(void);
unsigned char nondet_uchar(void);

#define MAXLEN ((size_t)1 << 48)
static const char *mkbuf(size_t *n)
{
  *n = nondet_size();
  __CPROVER_assume(*n < MAXLEN);
  char *b = malloc(*n);  // exact size: any read past the end fails --pointer-check
  return b;
}

void h_unpack_string(void)
{
  size_t n; const char *b = mkbuf(&n);
  const char *d = b; size_t s = n;
  String r = unpack_string(&d, &s);
  size_t hdr; uint64_t len;
  int ok = ref_strhdr((const unsigned char *)b, n, &hdr, &len) && len <= n - hdr;
  if (ok) {
    assert(r.data == b + hdr && r.size == len);
    assert(r.data != NULL);
    assert(d == b + hdr + len && s == n - hdr - len);
  } else {
    assert(r.data == NULL && r.size == 0);
    assert(d == b && s == n);  // "Data and size are preserved in case of failure"
  }
}

void h_unpack_array(void)
{
  size_t n; const char *b = mkbuf(&n);
  const char *d = b; size_t s = n;
  ssize_t r = unpack_array(&d, &s);
  size_t hdr; uint64_t len;
  int ok = ref_arrhdr((const unsigned char *)b, n, &hdr, &len);
  if (ok) {
    assert(r >= 0 && (uint64_t)r == len);
    assert(d == b + hdr && s == n - hdr);
  } else {
    assert(r == -1);
    assert(s <= n && d == b + (n - s));
  }
}

void h_unpack_integer(void)
{
  size_t n; const char *b = mkbuf(&n);
  const char *d = b; size_t s = n;
  Integer res = (Integer)nondet_size(), res0 = res;
  bool r = unpack_integer(&d, &s, &res);
  size_t hdr; int64_t val; int wrapped;
  int ok = ref_int((const unsigned char *)b, n, &hdr, &val, &wrapped);
  if (ok) {
    assert(r && res == val);
    assert(d == b + hdr && s == n - hdr);
  } else {
    assert(!r && res == res0);
    assert(s <= n && d == b + (n - s));
  }
}

// unpack_uint_or_sint on any token the real reader can produce (token taken from mpack_rtoken).
void h_unpack_uint_or_sint(void)
{
  size_t n; const char *b = mkbuf(&n);
  const char *d = b; size_t s = n;
  mpack_token_t tok;
  if (mpack_rtoken(&d, &s, &tok) != MPACK_OK) return;
  Integer res = (Integer)nondet_size(), res0 = res;
  bool r = unpack_uint_or_sint(tok, &res);
  size_t hdr; int64_t val; int wrapped;
  if (ref_int((const unsigned char *)b, n, &hdr, &val, &wrapped)) {
    assert(r && res == val);
  } else {
    assert(!r && res == res0);
  }
}

void h_parse_nop(void)
{
  parse_nop(NULL, NULL);  // empty body: nothing read or written
}
