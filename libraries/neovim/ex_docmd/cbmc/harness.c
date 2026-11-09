#include <stdlib.h>
// CBMC harnesses: verbatim upstream code (upstream.c, from build.py) against spec.h.
// Strings are exact-size objects of N bytes (last byte NUL, earlier bytes arbitrary,
// so any shorter string is covered too); any read past the object fails --bounds-check.
#include "upstream.c"
#include "spec.h"
#ifndef N
#define N 8
#endif
#ifndef M
#define M 5
#endif
char nondet_char(void);
int nondet_int(void);
_Bool nondet_bool(void);

static char *mkstr(int n) {
  char *s = malloc(n);
  __CPROVER_assume(s != NULL);  // harness allocation only, not a property of the code
  for (int i = 0; i < n - 1; i++) s[i] = nondet_char();
  s[n - 1] = 0;
  return s;
}

void h_ends_excmd(void) {
  int c = nondet_int();
  __CPROVER_assert((ends_excmd(c) != 0) == ref_ends_excmd(c), "ends_excmd matches spec");
}

void h_skipwhite(void) {
  char *s = mkstr(N);
  __CPROVER_assert(skipwhite(s) == s + ref_skipwhite(s), "skipwhite matches spec");
}

void h_find_nextcmd(void) {
  char *s = mkstr(N);
  int r = ref_find_nextcmd(s);
  char *got = find_nextcmd(s);
  __CPROVER_assert(r < 0 ? got == NULL : got == s + r, "find_nextcmd matches spec");
}

void h_check_nextcmd(void) {
  char *s = mkstr(N);
  int r = ref_check_nextcmd(s);
  char *got = check_nextcmd(s);
  __CPROVER_assert(r < 0 ? got == NULL : got == s + r, "check_nextcmd matches spec");
}

void h_skip_colon_white(void) {
  char *s = mkstr(N);
  bool lead = nondet_bool();
  char *got = skip_colon_white(s, lead);
  __CPROVER_assert(got == s + ref_skip_colon_white(s, lead), "skip_colon_white matches spec");
}

void h_checkforcmd(void) {
  char *s = mkstr(N);
  char *cmd = mkstr(M);
  int len = nondet_int();
  char *p = s;
  bool ok = checkforcmd(&p, cmd, len);
  int r = ref_checkforcmd(s, cmd, len);
  __CPROVER_assert(ok == (r >= 0), "checkforcmd result matches spec");
  __CPROVER_assert(ok ? p == s + r : p == s, "checkforcmd pointer matches spec");
}

void h_skipdigits(void) {
  char *s = mkstr(N);
  __CPROVER_assert(skipdigits(s) == s + ref_skipdigits(s), "skipdigits matches spec");
}

void h_modifier_len(void) {
  char *s = mkstr(N);
  __CPROVER_assert(modifier_len(s) == ref_modifier_len(s), "modifier_len matches spec");
}

void h_parse_bang(void) {
  char *s = mkstr(N);
  exarg_T ea;
  ea.cmdidx = nondet_int();
  char *p = s;
  bool got = parse_bang(&ea, &p);
  int r = ref_parse_bang(ea.cmdidx, s[0]);
  __CPROVER_assert(got == (r != 0), "parse_bang result matches spec");
  __CPROVER_assert(p == s + (r != 0), "parse_bang cursor matches spec");
}

// Memory safety for every input; the result is checked wherever the doc comment decides it.
void h_one_letter_cmd(void) {
  char *s = mkstr(N);
  cmdidx_T idx = nondet_int(), before = idx;
  int got = one_letter_cmd(s, &idx);
  int r = ref_one_letter_cmd(s);
  if (r >= 0) {
    __CPROVER_assert(got == (r != 0), "one_letter_cmd result matches spec");
    __CPROVER_assert(r == 1 ? idx == CMD_k : r == 2 ? idx == CMD_substitute : idx == before,
                     "one_letter_cmd index matches spec");
  } else {
    __CPROVER_assert(got ? idx == CMD_substitute : idx == before, "one_letter_cmd sets :s or nothing");
  }
}
