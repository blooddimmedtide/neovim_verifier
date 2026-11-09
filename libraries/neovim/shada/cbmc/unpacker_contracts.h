// MessagePack-unpacker contracts for verifying shada_read_next_item.
//
// unpack_string / unpack_array / unpack_integer are PROVED (CBMC, every byte
// content, every buffer length < 2^48, both char signednesses) by the unpacker
// thread in neovim_verifier PR #14, branch claude/project-thread-3l219g,
// libraries/neovim/unpacker/cbmc/ (status: candidate, owner sign-off pending).
// Modelled here as CBMC stubs that reproduce exactly those proved post-conditions,
// so a shada_read_next_item harness composes proved behaviour, not guesses.
//
// unpack_skip is NOT proved (it wraps mpack_parse, an unbounded loop that needs
// WP). It is the ONE assumed contract; every harness that calls it must be
// labelled as relying on an unproved callee until PR #14 closes unpack_skip.
//
// On entry let b = *data, n = *size. Every read stays inside [b, b+n).
#pragma once
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

typedef struct { char *data; size_t size; } String;
typedef int64_t Integer;

size_t nondet_size_t(void);
unsigned char nondet_uchar(void);
int64_t nondet_i64(void);

// unpack_string: on a str/bin header (a0-bf, d9-db, c4-c6) for payload length L
// with hdr+L <= n, returns {b+hdr, L} (non-NULL even when L==0) and consumes
// hdr+L; otherwise returns {NULL,0} with *data,*size unchanged.
static inline String unpack_string(const char **data, size_t *size)
{
  const char *b = *data; size_t n = *size;
  if (nondet_uchar() & 1) {               // models "valid header with hdr+L<=n"
    size_t hdr = nondet_size_t(), L = nondet_size_t();
    __CPROVER_assume(hdr >= 1 && hdr <= 5);
    __CPROVER_assume(hdr <= n && L <= n - hdr);
    *data = b + hdr + L; *size = n - hdr - L;
    String s = { (char *)(b + hdr), L };  // non-NULL
    return s;
  }
  String s = { NULL, 0 };                  // *data,*size unchanged
  return s;
}

// unpack_array: on an array header returns the count and consumes exactly the
// header; otherwise returns -1 with only *size <= n, *data == b+(n-*size).
static inline int64_t unpack_array(const char **data, size_t *size)
{
  const char *b = *data; size_t n = *size;
  if (nondet_uchar() & 1) {
    size_t hdr = nondet_size_t(); __CPROVER_assume(hdr >= 1 && hdr <= 5 && hdr <= n);
    int64_t count = nondet_i64(); __CPROVER_assume(count >= 0 && count <= 0xFFFFFFFF);
    *data = b + hdr; *size = n - hdr;
    return count;
  }
  size_t left = nondet_size_t(); __CPROVER_assume(left <= n);
  *size = left; *data = b + (n - left);
  return -1;
}

// unpack_integer: on a complete integer returns true, sets *res, consumes it;
// otherwise false, *res untouched, same failure guarantee as unpack_array.
static inline bool unpack_integer(const char **data, size_t *size, Integer *res)
{
  const char *b = *data; size_t n = *size;
  if (nondet_uchar() & 1) {
    size_t hdr = nondet_size_t(); __CPROVER_assume(hdr >= 1 && hdr <= 9 && hdr <= n);
    *res = nondet_i64();                   // any value (uint64 >= 2^63 wraps to value-2^64)
    *data = b + hdr; *size = n - hdr;
    return true;
  }
  size_t left = nondet_size_t(); __CPROVER_assume(left <= n);
  *size = left; *data = b + (n - left);
  return false;                            // *res untouched
}

// unpack_skip: ASSUMED (unproved). On OK it consumed exactly one complete value;
// never reads outside [b,b+n). Returns 0 (OK) / 1 (EOF) / 2 (ERROR) / 3 (NOMEM).
static inline int unpack_skip(const char **data, size_t *size)
{
  const char *b = *data; size_t n = *size;
  int r = (int)(nondet_uchar() & 3);
  if (r == 0) { size_t used = nondet_size_t(); __CPROVER_assume(used >= 1 && used <= n);
                *data = b + used; *size = n - used; }
  return r;
}
