// CBMC harness for trunc_string (src/nvim/message.c), verbatim extraction.
// Model: input bytes are ASCII (1..127). Under 'encoding=utf-8' ASCII bytes
// are one-byte characters: utfc_ptr2len = 1, utf_head_off = 0, and
// ptr2cells = 2 for control characters (shown as ^X) else 1.
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdbool.h>
#define NUL '\0'
static int ptr2cells(const char *p) { unsigned char c = (unsigned char)*p; return (c < 0x20 || c == 0x7f) ? 2 : 1; }
static int utfc_ptr2len(const char *p) { return *p == NUL ? 0 : 1; }
static int utf_head_off(const char *base, const char *p) { (void)base; (void)p; return 0; }
#include "trunc_string.c"
#ifndef CHECKSPEC
#define CHECKSPEC 1
#endif
#ifndef SN
#define SN 8
#endif
#ifndef BN
#define BN 10
#endif
int nondet_int(void);
unsigned char nondet_uchar(void);
int main(void) {
  int slen = nondet_int();
  __CPROVER_assume(slen >= 0 && slen < SN);
  char *s = malloc((size_t)slen + 1); __CPROVER_assume(s != NULL);
  for (int k = 0; k < slen; k++) { unsigned char c = nondet_uchar(); __CPROVER_assume(c >= 1 && c <= 127); s[k] = (char)c; }
  s[slen] = NUL;
  int room_in = nondet_int();
  __CPROVER_assume(room_in >= -2 && room_in <= BN + 2);
  int buflen = nondet_int();
  __CPROVER_assume(buflen >= MINBUF && buflen <= BN);
  char *orig = malloc((size_t)slen + 1); __CPROVER_assume(orig != NULL); memcpy(orig, s, (size_t)slen + 1);
#ifdef ALIAS
  __CPROVER_assume(buflen <= slen + 1);
  char *buf = s;
#else
  char *buf = malloc((size_t)buflen); __CPROVER_assume(buf != NULL);
#endif
  trunc_string(s, buf, room_in, buflen);
  if (CHECKSPEC && buflen >= 1) {
    // Result is a C string inside the buffer.
    int t = -1;
    for (int k = 0; k < buflen; k++) { if (buf[k] == NUL) { t = k; break; } }
    assert(t >= 0);
#ifndef ALIAS
    // Reference: if s fits in buf, and its width <= room_in, the result is s.
    int w = 0; for (int k = 0; k < slen; k++) w += ptr2cells(orig + k);
    if (slen < buflen && w <= room_in) assert(t == slen && memcmp(buf, orig, (size_t)slen) == 0);
    // Otherwise the result is a prefix of s, optionally followed by "..." and a suffix of s.
    if (t != slen || memcmp(buf, orig, (size_t)slen) != 0) {
      int d = -1;
      for (int k = 0; k + 2 < t; k++) if (buf[k] == '.' && buf[k+1] == '.' && buf[k+2] == '.' && memcmp(buf, orig, (size_t)k) == 0 && k <= slen) {
        int rest = t - k - 3; if (rest <= slen && memcmp(buf + k + 3, orig + slen - rest, (size_t)rest) == 0) { d = k; break; } }
      int prefix_only = t <= slen && memcmp(buf, orig, (size_t)t) == 0;
      assert(d >= 0 || prefix_only);
    }
#endif
  }
  return 0;
}
