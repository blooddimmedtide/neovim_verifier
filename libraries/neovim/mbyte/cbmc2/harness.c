// Round 2 CBMC proofs for more UTF-8 helpers in src/nvim/mbyte.c. Same method
// as ../cbmc: nondeterministic inputs, exact-size objects (so any read past
// them fails --pointer-check), references from ../cbmc/spec.h (RFC 2279/3629).
#include <stdint.h>
#include <stdlib.h>
#include "../cbmc/spec.h"
#include MBYTE_UTF8_C
int nondet_int(void); size_t nondet_size(void);

// NUL-terminated string of nondet length 0..max, object of exactly len+1 bytes.
static char *any_str(int max, int *len) {
  int n = nondet_int(); __CPROVER_assume(0 <= n && n <= max);
  char *s = malloc((size_t)n + 1);
  for (int i = 0; i < n; i++) __CPROVER_assume(s[i] != 0);
  s[n] = 0; *len = n; return s;
}

// utf_ptr2CharInfo_impl(p, len), as its caller utf_ptr2CharInfo (mbyte.h) uses
// it: p is a NUL-terminated string, p[0] >= 0x80, len = utf8len_tab[p[0]].
// Result: the value of a complete sequence, a negative number otherwise.
static void check_impl(const uint8_t *p) {
  int L = spec_lead_len(p[0]);
  bool ok = L >= 2;
  for (int k = 1; ok && k < L; k++) if (!spec_is_cont(p[k])) ok = false;
  int32_t r = utf_ptr2CharInfo_impl(p, (uintptr_t)utf8len_tab[p[0]]);
  if (ok) __CPROVER_assert(r == (int32_t)spec_value(p, L), "complete: value");
  else __CPROVER_assert(r < 0, "incomplete or bad lead: negative");
}
void h_charinfo_impl(void) {
  int n; char *s = any_str(6, &n);
  __CPROVER_assume((uint8_t)s[0] >= 0x80);
  check_impl((const uint8_t *)s);
}
void h_charinfo_impl_long(void) {   // strings of 7+ bytes: 6 nonzero bytes suffice
  char *s = malloc(6);
  for (int i = 0; i < 6; i++) __CPROVER_assume(s[i] != 0);
  __CPROVER_assume((uint8_t)s[0] >= 0x80);
  check_impl((const uint8_t *)s);
}

// mb_cptr2char_adv: returns the character at *pp and moves *pp past its bytes
// (0 bytes for "", the sequence length otherwise).
void h_cptr2char_adv(void) {
  int n; char *s = any_str(6, &n);
  const char *p = s;
  int c = mb_cptr2char_adv(&p);
  __CPROVER_assert(c == ref_ptr2char((const uint8_t *)s), "char");
  __CPROVER_assert(p == s + ref_ptr2len((const uint8_t *)s), "advance");
}
void h_cptr2char_adv_long(void) {
  char *s = malloc(6);
  for (int i = 0; i < 6; i++) __CPROVER_assume(s[i] != 0);
  const char *p = s;
  int c = mb_cptr2char_adv(&p);
  __CPROVER_assert(c == ref_ptr2char((const uint8_t *)s), "char (long)");
  __CPROVER_assert(p == s + ref_ptr2len((const uint8_t *)s), "advance (long)");
}

// utf_safe_read_char_adv(s, n): reads one character from a buffer of n bytes
// (not NUL-terminated). n == 0: returns 0, nothing changes. ASCII (and NUL):
// returns it, advances 1. A complete sequence of L <= n bytes: returns its
// value, advances L. Otherwise (cut off by n, bad lead, bad trail): -1, nothing
// changes. The object holds exactly min(n, 6) bytes, so reads past n fail.
void h_safe_read(void) {
  size_t n = nondet_size();
  size_t obj = n < 1 ? 1 : n > 6 ? 6 : n;
  char *buf = malloc(obj);
  const uint8_t *u = (const uint8_t *)buf;
  const char *s = buf; size_t m = n;
  int r = utf_safe_read_char_adv(&s, &m);
  if (n == 0) { __CPROVER_assert(r == 0 && s == buf && m == 0, "empty"); return; }
  if (u[0] < 0x80) { __CPROVER_assert(r == u[0] && s == buf + 1 && m == n - 1, "ascii"); return; }
  int L = spec_lead_len(u[0]);
  bool ok = L >= 2 && (size_t)L <= n;
  for (int k = 1; ok && k < L; k++) if (!spec_is_cont(u[k])) ok = false;
  if (ok) __CPROVER_assert(r == (int)spec_value(u, L) && s == buf + L && m == n - (size_t)L, "complete");
  else __CPROVER_assert(r == -1 && s == buf && m == n, "bad: -1, unchanged");
}
