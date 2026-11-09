// CBMC harnesses for src/nvim/tag.c tag-line helpers. Every string lives in an
// object of exactly its size, so any read past it fails the pointer checks.
#include "tag_extract.c"
#include "spec.h"
#include <stdlib.h>
#ifndef N
#define N 8
#endif
size_t nondet_size(void);
char nondet_char(void);

static char *nondet_cstr(size_t *len_out)
{ // NUL-terminated string in an object of exactly n bytes, 1 <= n <= N
  size_t n = nondet_size();
  __CPROVER_assume(n >= 1 && n <= N);
  char *s = malloc(n);
  __CPROVER_assume(s != NULL);
  for (size_t i = 0; i < n; i++) s[i] = nondet_char();
  __CPROVER_assume(s[n - 1] == NUL);
  *len_out = n;
  return s;
}

void h_parse_tag_line(void)
{
  size_t n; char *s = nondet_cstr(&n);
  size_t sl = strlen(s);           // s may contain an earlier NUL: the line ends there
  tagptrs_T t;
  int r = parse_tag_line(s, &t);
  size_t t1 = spec_index_of(s, 0, sl + 1, TAB);
  size_t t2 = t1 < sl ? spec_index_of(s, t1 + 1, sl + 1, TAB) : sl + 1;
  bool ok = t1 < sl && t2 < sl && s[t2 + 1] != NUL;
  assert(r == (ok ? OK : FAIL));
  assert(t.tagname == s);
  if (t1 < sl) assert(t.tagname_end == s + t1 && t.fname == s + t1 + 1);
  if (t1 < sl && t2 < sl) assert(t.fname_end == s + t2);
  if (ok) assert(t.command == s + t2 + 1);
}

void h_tag_strnicmp(void)
{
  size_t n1, n2; char *a = nondet_cstr(&n1); char *b = nondet_cstr(&n2);
  size_t len = nondet_size(); __CPROVER_assume(len <= N + 1);
  int r = tag_strnicmp(a, b, len);
  // reference: first i < len where folded bytes differ, stopping after a common NUL
  int want = 0;
  for (size_t i = 0; i < len; i++) {
    int d = spec_upper((unsigned char)a[i]) - spec_upper((unsigned char)b[i]);
    if (d != 0) { want = d; break; }
    if (a[i] == NUL) break;
  }
  assert(r == want);
}

void h_test_for_static(void)
{
  size_t n; char *s = nondet_cstr(&n);
  size_t off = nondet_size(); __CPROVER_assume(off < n);
  tagptrs_T t; t.command = s + off;
  bool r = test_for_static(&t);
  size_t sl = strlen(s);
  bool want = false;   // some TAB at i >= off (before the NUL) followed by "file:"
  for (size_t i = off; i < sl; i++)
    if (s[i] == '\t' && i + 5 < sl + 1 && s[i+1]=='f' && s[i+2]=='i' && s[i+3]=='l'
        && s[i+4]=='e' && s[i+5]==':') want = true;
  assert(r == want);
}

void h_matching_line_len(void)
{ // documented layout: <mtt><tag_fname><NUL>...<lbuf><NUL>, object ends at last NUL
  size_t n; char *s = nondet_cstr(&n);
  __CPROVER_assume(n >= 3);
  size_t k = spec_index_of(s, 1, n, NUL);
  __CPROVER_assume(k < n - 1);    // a NUL after tag_fname, then more bytes
  size_t j = spec_index_of(s, k + 1, n, NUL);
  assert(matching_line_len(s) == j);
}
