#include <stdlib.h>
#include "quickfix_efm.c"
#include "spec.h"
#ifndef LEN
#define LEN 4
#endif
char nondet_char(void);
size_t nondet_size(void);

// Exact-size, NUL-terminated nondeterministic string of length n <= MAXLEN.
static char *mkstr(size_t *pn) {
  size_t n = LEN;  // one CBMC run per concrete length 0..MAXLEN (exact-size object)
  char *s = malloc(n + 1);
  __CPROVER_assume(s != NULL);  // xmalloc never returns NULL
  for (size_t i = 0; i < n; i++) { s[i] = nondet_char(); __CPROVER_assume(s[i] != 0); }
  s[n] = 0;
  *pn = n;
  return s;
}

void check_part_len(void) {
  size_t n; char *s = mkstr(&n);
  int len = efm_option_part_len(s);
  assert(len == ref_part_len(s));
  assert(len >= 0 && (size_t)len <= n);
}

void check_analyze_prefix(void) {
  size_t n; char *s = mkstr(&n);
  __CPROVER_assume(n >= 1);
  efm_T fmt; memset(&fmt, 0, sizeof fmt);
  const char *r = efm_analyze_prefix(s, &fmt);
  int fl = ref_is_flag(s[0]);
  char p = s[fl ? 1 : 0];
  if (ref_is_prefix(p) && p != 0) {
    assert(r == s + (fl ? 1 : 0));
    assert(fmt.prefix == p);
    assert(fmt.flags == (fl ? s[0] : 0));
  } else {
    assert(r == NULL);
  }
}

// parse_efm_option's use: buffer of efm_regpat_bufsz(whole option) bytes, one part at a time,
// fresh zeroed efm_T per part. Exact-size buffer: any write past it fails the pointer checks.
void check_to_regpat(void) {
  size_t n; char *efm = mkstr(&n);
  size_t sz = efm_regpat_bufsz(efm);
  char *buf = malloc(sz);
  __CPROVER_assume(buf != NULL);  // xmalloc never returns NULL
  int len = efm_option_part_len(efm);
  efm_T fmt; memset(&fmt, 0, sizeof fmt);
  int r = efm_to_regpat(efm, len, &fmt, buf);
  if (r == OK) {
    assert(buf[0] == '^');
    // (Output length is not checked here; the claim is memory safety of every write.)
  }
}
