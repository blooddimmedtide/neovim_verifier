// CBMC harness: check_regexp_delim (src/nvim/ex_cmds.c) and its two call sites.
// Spec (":help E146"): a letter can't delimit a pattern: return FAIL and give E146 exactly once
// for a letter, OK and no message otherwise. C11 7.4p1: the argument of isalpha must be EOF or
// representable as unsigned char, otherwise the behavior is undefined.
// __NO_CTYPE (set by run_delim.sh) makes isalpha a call to CBMC's C-locale model, not glibc's table macro.
#include <ctype.h>
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#define OK 1
#define FAIL 0
#define _(s) (s)
static int n_emsg; static bool e146;
static bool emsg(const char *m) { n_emsg++; e146 = strncmp(m, "E146:", 5) == 0; return true; }
#include DELIM_C
int nondet_int(void); char nondet_char(void);
static bool ref_letter(int c) { return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'); }
void h_check_regexp_delim(void)   // every argument isalpha accepts, C locale
{
  int c = nondet_int(); __CPROVER_assume(c == EOF || (c >= 0 && c <= 255));
  n_emsg = 0; e146 = false;
  int r = check_regexp_delim(c);
  __CPROVER_assert(r == (ref_letter(c) ? FAIL : OK), "FAIL exactly for letters");
  __CPROVER_assert(n_emsg == (r == FAIL) && e146 == (r == FAIL), "E146 exactly on FAIL");
}
void h_call_sites(void)   // the byte *cmd passed by do_sub and ex_global keeps isalpha defined
{
  char b[2] = { nondet_char(), 0 };
  int a0 = call_site_0(b), a1 = call_site_1(b);
  __CPROVER_assert(a0 == EOF || (a0 >= 0 && a0 <= 255), "do_sub: isalpha argument in domain");
  __CPROVER_assert(a1 == EOF || (a1 >= 0 && a1 <= 255), "ex_global: isalpha argument in domain");
}
