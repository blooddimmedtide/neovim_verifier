// CBMC harness: sub_parse_flags (src/nvim/ex_cmds.c) against spec.h for every string up to
// LEN-1 bytes, every starting flag state, both 'gdefault' values, both char signednesses.
#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>
#define NUL '\0'
typedef enum { kSubHonorOptions = 0, kSubIgnoreCase, kSubMatchCase } SubIgnoreType;
typedef struct { bool do_all, do_ask, do_count, do_error, do_print, do_list, do_number;
                 SubIgnoreType do_ic; } subflags_T;
enum { RE_SEARCH = 0, RE_SUBST = 1, RE_LAST = 2, RE_BOTH = 3 };
bool p_gd;
#include SUB_C
#include "spec.h"
#ifndef LEN
#define LEN 9
#endif
bool nondet_bool(void); int nondet_int(void); char nondet_char(void); size_t nondet_size(void);
void h_sub_parse_flags(void)
{
  size_t n = nondet_size(); __CPROVER_assume(n >= 1 && n <= LEN);
  char *cmd = malloc(n);            // exact size: reading past the NUL fails the bounds check
  for (size_t i = 0; i + 1 < n; i++) cmd[i] = nondet_char();
  cmd[n - 1] = NUL;
  p_gd = nondet_bool();
  subflags_T s = { nondet_bool(), nondet_bool(), nondet_bool(), nondet_bool(), nondet_bool(), nondet_bool(), nondet_bool(),
                   (SubIgnoreType)(nondet_int() % 3 + 3) % 3 };
  ref_flags r = { s.do_all, s.do_ask, s.do_count, s.do_error, s.do_print, s.do_list,
                  s.do_number, (int)s.do_ic };
  int w = nondet_int(), rw = w;
  char *ret = sub_parse_flags(cmd, &s, &w);
  const char *rret = ref_parse(cmd, &r, &rw, p_gd, RE_LAST, kSubHonorOptions, kSubIgnoreCase,
                               kSubMatchCase);
  __CPROVER_assert(ret == rret, "end pointer matches reference");
  __CPROVER_assert(ret >= cmd && ret < cmd + n, "result inside the string");
  __CPROVER_assert(s.do_all == r.all && s.do_ask == r.ask && s.do_count == r.count
                   && s.do_error == r.error && s.do_print == r.print && s.do_list == r.list
                   && s.do_number == r.number && (int)s.do_ic == r.ic, "flags match reference");
  __CPROVER_assert(w == rw, "which_pat matches reference");
  __CPROVER_assert(!(s.do_count && s.do_ask), "count-only never asks");
}
