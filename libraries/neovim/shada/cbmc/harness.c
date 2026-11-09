// CBMC harnesses for the ShaDa reading primitives of src/nvim/shada.c.
// The code under test is the verbatim extraction SHADA_READ_C (build.py).
#include SHADA_READ_C
#include "spec.h"

// Typed nondeterministic generators (CBMC built-ins), so the harness's own
// value construction never trips the conversion/overflow checks that guard the
// code under test.
unsigned char nondet_uchar(void);
unsigned int nondet_uint(void);
unsigned long nondet_ulong(void);

#define MAXN 12   // file bytes considered: covers every format (1 + 8) plus slack

static unsigned char filebuf[MAXN];

static void init_file(FileDescriptor *fp, size_t *n)
{
  *n = nondet_size_t();
  __CPROVER_assume(*n <= MAXN);
  for (size_t i = 0; i < MAXN; i++) filebuf[i] = nondet_uchar();
  fp->data = filebuf;
  fp->size = *n;
  fp->pos = 0;
  fp->bytes_read = nondet_ulong();   // any start offset
  __CPROVER_assume(fp->bytes_read < ((uint64_t)1 << 62));
  fp->eof = false;
  fp->fail_errno = nondet_int();
  __CPROVER_assume(fp->fail_errno < 0);
  fp->fail_on = (int)(nondet_uint() % 4u);  // 0..3
  (void)0;
  fp->calls = 0;
}

// vim_be64toh: the bytes of x in memory order, read as a big-endian number.
void h_be64toh(void)
{
  uint64_t x = ((uint64_t)nondet_uint() << 32) | (uint64_t)nondet_uint();
  unsigned char b[8];
  memcpy(b, &x, 8);
  assert(vim_be64toh(x) == spec_be(b, 8));
}

// msgpack_read_uint64: full functional spec against the reference.
void h_read_uint64(void)
{
  FileDescriptor fd; size_t n; init_file(&fd, &n);
  bool allow_eof = nondet_int() != 0;
  uint64_t start = fd.bytes_read;
  uint64_t result = 0x5a5a5a5a5a5a5a5aULL, before = result;
  ShaDaReadResult r = msgpack_read_uint64(&fd, allow_eof, &result);

  assert(fd.pos <= n);
  assert(fd.bytes_read == start + fd.pos);          // counter tracks what was consumed
  if (fd.fail_on == 1) {                            // first read fails
    assert(r == kSDReadStatusReadError && result == before);
    return;
  }
  if (n == 0) {                                     // nothing to read
    assert(r == (allow_eof ? kSDReadStatusFinished : kSDReadStatusNotShaDa));
    assert(result == before && fd.pos == 0);
    return;
  }
  int k = spec_uint_payload(filebuf[0]);
  if (k < 0) {                                      // not an unsigned integer
    assert(r == kSDReadStatusNotShaDa && result == before && fd.pos == 1);
    return;
  }
  if (k == 0) {
    assert(r == kSDReadStatusSuccess && result == filebuf[0] && fd.pos == 1);
    return;
  }
  if (fd.fail_on == 2) {
    assert(r == kSDReadStatusReadError && result == before);
    return;
  }
  if (n < 1 + (size_t)k) {                          // payload cut off by EOF
    assert(r == kSDReadStatusNotShaDa && result == before && fd.pos == n);
    return;
  }
  assert(r == kSDReadStatusSuccess);
  assert(result == spec_be(filebuf + 1, k));        // exact value
  assert(fd.pos == 1 + (size_t)k);                  // reads exactly what it needs
}

// fread_len: success iff exactly length bytes were read; they land in buffer.
void h_fread_len(void)
{
  FileDescriptor fd; size_t n; init_file(&fd, &n);
  size_t len = nondet_size_t();
  __CPROVER_assume(len <= MAXN);
  char *buf = malloc(len);                          // exact-size object
  ShaDaReadResult r = fread_len(&fd, buf, len);
  if (fd.fail_on == 1) { assert(r == kSDReadStatusReadError); return; }
  if (n < len) { assert(r == kSDReadStatusNotShaDa && fd.pos == n); return; }
  assert(r == kSDReadStatusSuccess && fd.pos == len);
  unsigned char *ubuf = (unsigned char *)buf;
  for (size_t i = 0; i < len; i++) assert(ubuf[i] == filebuf[i]);
}

// sd_reader_skip: success iff offset bytes were skipped.
void h_skip(void)
{
  FileDescriptor fd; size_t n; init_file(&fd, &n);
  size_t off = nondet_size_t();
  __CPROVER_assume(off <= PTRDIFF_MAX);  // caller checks length <= PTRDIFF_MAX
  ShaDaReadResult r = sd_reader_skip(&fd, off);
  if (fd.fail_on == 1) { assert(r == kSDReadStatusReadError); return; }
  if (n < off) { assert(r == kSDReadStatusNotShaDa && fd.pos == n); return; }
  assert(r == kSDReadStatusSuccess && fd.pos == off);
}

// shada_check_status: classifies an unpack result. Success only when the parse
// succeeded (MPACK_OK) and consumed every byte of the item (remaining == 0);
// every other case is NotShaDa. (initial_fpos only affects the message.)
void h_check_status(void)
{
  uint64_t fpos = ((uint64_t)nondet_uint() << 32) | (uint64_t)nondet_uint();
  int status = nondet_int();
  size_t remaining = nondet_ulong();
  ShaDaReadResult r = shada_check_status(fpos, status, remaining);
  if (status == MPACK_OK && remaining == 0) {
    assert(r == kSDReadStatusSuccess);
  } else {
    assert(r == kSDReadStatusNotShaDa);
  }
}
