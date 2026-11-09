// Independent reference, written from the MessagePack specification
// (https://github.com/msgpack/msgpack/blob/master/spec.md, "int format family"),
// not from shada.c. Only the unsigned formats are accepted, as the function's
// documentation says ("Errors out if the result is not an unsigned integer").
#pragma once
#include <stdint.h>
#include <stddef.h>
// Length of the payload after first byte b, or -1 if b does not start an
// unsigned integer. Positive fixint 0x00..0x7f has no payload.
static int spec_uint_payload(unsigned char b)
{
  if (b <= 0x7f) return 0;
  if (b == 0xcc) return 1;
  if (b == 0xcd) return 2;
  if (b == 0xce) return 4;
  if (b == 0xcf) return 8;
  return -1;
}
// Big-endian value of p[0..n) (the payload is big-endian per the spec).
static uint64_t spec_be(const unsigned char *p, int n)
{
  uint64_t v = 0;
  for (int i = 0; i < n; i++) v = v * 256 + p[i];
  return v;
}
