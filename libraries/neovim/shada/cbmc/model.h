// Abstract model of Neovim's FileDescriptor (src/nvim/os/fileio.c) for a file
// opened for reading in blocking mode, which is how shada.c opens it.
// The file is the byte array data[0..size). file_read copies
// min(len, size - pos) bytes, advances pos and bytes_read, and sets eof when
// it asked for more than was left (a blocking read only stops early at EOF).
// Call number fail_on may instead fail with a negative errno, consuming an
// unknown number of bytes, as os_read can. file_skip is the same without a copy.
#pragma once
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>

typedef struct {
  const unsigned char *data;
  size_t size;
  size_t pos;
  uint64_t bytes_read;
  bool eof;
  int fail_errno;  // < 0: errno the failing call returns
  int fail_on;     // 1-based index of the call that fails, 0 = none
  int calls;
} FileDescriptor;

int nondet_int(void);
size_t nondet_size_t(void);

static inline ptrdiff_t model_take(FileDescriptor *fp, char *dst, size_t len)
{
  fp->calls++;
  if (fp->calls == fp->fail_on) {
    int e = fp->fail_errno;
    size_t junk = nondet_size_t();
    __CPROVER_assume(junk <= fp->size - fp->pos);
    fp->pos += junk; fp->bytes_read += junk;
    return e;
  }
  size_t left = fp->size - fp->pos;
  size_t n = len < left ? len : left;
  if (dst != NULL && n > 0) {
    memcpy(dst, fp->data + fp->pos, n);
  }
  fp->pos += n; fp->bytes_read += n;
  if (n < len) {
    fp->eof = true;
  }
  return (ptrdiff_t)n;
}

static inline ptrdiff_t file_read(FileDescriptor *fp, char *buf, size_t len)
{
  return model_take(fp, buf, len);
}
static inline ptrdiff_t file_skip(FileDescriptor *fp, size_t len)
{
  return model_take(fp, NULL, len);
}
static inline bool file_eof(const FileDescriptor *fp)
{
  return fp->eof;
}
static inline void semsg(const char *fmt, ...) { (void)fmt; }
static inline const char *os_strerror(int e) { (void)e; return "error"; }
