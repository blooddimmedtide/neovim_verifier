#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define MIN(a, b) ((a) < (b) ? (a) : (b))
typedef int32_t linenr_T;
typedef struct s_mmfile { char *ptr; int size; } mmfile_t;
/* C11 7.24.5.1 memchr model: first byte equal to (unsigned char)c in s[0..n), else NULL.
   It reads each byte it scans, so a read past the object fails the pointer check. */
void *memchr(const void *s, int c, size_t n) {
  const unsigned char *p = s;
  for (size_t i = 0; i < n; i++) if (p[i] == (unsigned char)c) return (void *)(p + i);
  return NULL;
}
#include LINEMATCH_C
#include "spec.h"
#ifndef N
#define N 4
#endif
int nondet_int(void); char nondet_char(void); bool nondet_bool(void);

/* Exact-size buffer of n nondeterministic bytes: any read past it fails. */
static char *buf(int n) { char *p = malloc((size_t)n); for (int i = 0; i < n; i++) p[i] = nondet_char(); return p; }

void h_line_len(void) {
  int n = nondet_int(); __CPROVER_assume(n >= 0 && n <= N);
  mmfile_t m = { buf(n), n };
  __CPROVER_assert(line_len(&m) == ref_line_len(m.ptr, n), "line_len = spec");
}

/* matching_chars = LCS of the first lines (each cut to 799 bytes; here n <= N < 799). */
void h_matching_chars(void) {
  int n1 = nondet_int(), n2 = nondet_int();
  __CPROVER_assume(n1 >= 0 && n1 <= N && n2 >= 0 && n2 <= N);
  mmfile_t a = { buf(n1), n1 }, b = { buf(n2), n2 };
  int r = matching_chars(&a, &b);
  __CPROVER_assert(r == ref_lcs(a.ptr, (int)ref_line_len(a.ptr, n1), b.ptr, (int)ref_line_len(b.ptr, n2)),
                   "matching_chars = LCS of first lines");
}

/* matching_chars_iwhite = LCS of the first lines with ' ' and '\t' removed. */
void h_matching_chars_iwhite(void) {
  int n1 = nondet_int(), n2 = nondet_int();
  __CPROVER_assume(n1 >= 0 && n1 <= N && n2 >= 0 && n2 <= N);
  mmfile_t a = { buf(n1), n1 }, b = { buf(n2), n2 };
  int r = matching_chars_iwhite(&a, &b);
  char sa[N], sb[N]; int ka = 0, kb = 0;
  int la = (int)ref_line_len(a.ptr, n1), lb = (int)ref_line_len(b.ptr, n2);
  for (int i = 0; i < la; i++) if (a.ptr[i] != ' ' && a.ptr[i] != '\t') sa[ka++] = a.ptr[i];
  for (int i = 0; i < lb; i++) if (b.ptr[i] != ' ' && b.ptr[i] != '\t') sb[kb++] = b.ptr[i];
  __CPROVER_assert(r == ref_lcs(sa, ka, sb, kb), "iwhite = LCS without blanks");
}

/* fastforward_buf_to_lnum: skip lnum-1 lines; if the text runs out, ptr = NULL and size 0. */
void h_fastforward(void) {
  int n = nondet_int(); __CPROVER_assume(n >= 0 && n <= N);
  linenr_T lnum = nondet_int(); __CPROVER_assume(lnum > INT32_MIN && lnum <= N + 2);
  char *p = buf(n);
  mmfile_t r = fastforward_buf_to_lnum((mmfile_t){ p, n }, lnum);
  /* reference: position after the (lnum-1)-th '\n' */
  int pos = 0, ok = 1;
  for (int k = 0; k < lnum - 1 && ok; k++) {
    int i = pos; while (i < n && p[i] != '\n') i++;
    if (i == n) ok = 0; else pos = i + 1;
  }
  if (ok) __CPROVER_assert(r.ptr == p + pos && r.size == n - pos, "at line lnum");
  else __CPROVER_assert(r.ptr == NULL && r.size == 0, "ran out: NULL, 0");
}

/* count_n_matched_chars: sum of pairwise scores over non-NULL buffers,
   scaled by 2/pairs when 2 or more pairs matched (doc: "prioritize a match of 3 equally to 2"). */
void h_count_n(void) {
  size_t n = (size_t)nondet_int(); __CPROVER_assume(n <= 3);
  bool iw = nondet_bool();
  mmfile_t f[3]; mmfile_t *sp[3];
  for (size_t i = 0; i < n; i++) {
    int k = nondet_int(); __CPROVER_assume(k >= 0 && k <= 2);
    f[i].ptr = nondet_bool() ? buf(k) : NULL; f[i].size = k; sp[i] = &f[i];
  }
  int r = count_n_matched_chars(sp, n, iw);
  int sum = 0, pairs = 0;
  for (size_t i = 0; i < n; i++) for (size_t j = i + 1; j < n; j++)
    if (f[i].ptr && f[j].ptr) { pairs++; sum += iw ? matching_chars_iwhite(&f[i], &f[j]) : matching_chars(&f[i], &f[j]); }
  if (pairs >= 2) sum = sum * 2 / pairs;
  __CPROVER_assert(r == sum, "count_n = scaled pairwise sum");
}
