// CBMC harness: get_op, get_option_prefix, find_tty_option_end (src/nvim/option.c @ 7b87ce8).
// Input: nondeterministic NUL-terminated string in an exact-size object of N bytes,
// so any read past the terminator is an out-of-bounds failure.
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#define NUL '\0'
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_PURE
#define FUNC_ATTR_WARN_UNUSED_RESULT
typedef enum { OP_NONE = 0, OP_ADDING, OP_PREPENDING, OP_REMOVING } set_op_T;
typedef enum { PREFIX_NO = 0, PREFIX_NONE, PREFIX_INV } set_prefix_T;
static bool strequal(const char *a, const char *b)  // memory.c, verbatim body
{ return (a == NULL && b == NULL) || (a && b && strcmp(a, b) == 0); }
// Macros copied verbatim from macros_defs.h.
#define ASCII_ISLOWER(c) ((unsigned)(c) >= 'a' && (unsigned)(c) <= 'z')
#define ASCII_ISUPPER(c) ((unsigned)(c) >= 'A' && (unsigned)(c) <= 'Z')
#define ASCII_ISALPHA(c) (ASCII_ISUPPER(c) || ASCII_ISLOWER(c))
typedef int OptIndex;
#define kOptInvalid (-1)
// find_option_len (hash lookup in options[]) is not under proof here: the stub records its
// arguments and returns an arbitrary index, so the claim covers only the name scan.
static const char *fol_arg; static size_t fol_len; static int fol_calls;
int nondet_int(void);
static OptIndex find_option_len(const char *arg, size_t len)
{ fol_arg = arg; fol_len = len; fol_calls++; return nondet_int(); }
#include "extracted.c"
#include "spec.h"
#ifndef N
#define N 8
#endif
char nondet_char(void);
size_t nondet_size(void);
int main(void)
{
  size_t n = nondet_size();
  __CPROVER_assume(n >= 1 && n <= N);
  char *s = malloc(n);
  for (size_t i = 0; i < n; i++) s[i] = nondet_char();
  __CPROVER_assume(s[n - 1] == NUL);

  __CPROVER_assert(get_op(s) == ref_get_op(s, n), "get_op matches spec");

  char *p = s;
  size_t adv;
  set_prefix_T want = ref_prefix(s, n, &adv);
  set_prefix_T got = get_option_prefix(&p);
  __CPROVER_assert(got == want && p == s + adv, "get_option_prefix matches spec");

  long r = ref_tty_end(s, n);
  const char *e = find_tty_option_end(s);
  __CPROVER_assert(r < 0 ? e == NULL : e == s + r, "find_tty_option_end matches spec");
  __CPROVER_assert(is_tty_option(s) == (r >= 0), "is_tty_option matches spec");

  // find_option_end: tty names first; else a run of ASCII letters looked up by length.
  OptIndex idx = 12345; fol_calls = 0;
  const char *fe = find_option_end(s, &idx);
  if (r >= 0) {
    __CPROVER_assert(fe == s + r && idx == kOptInvalid && fol_calls == 0, "find_option_end tty");
  } else {
    size_t a = ref_alpha_run(s, n);
    if (a == 0) __CPROVER_assert(fe == NULL && idx == kOptInvalid && fol_calls == 0, "find_option_end no name");
    else __CPROVER_assert(fe == s + a && fol_calls == 1 && fol_arg == s && fol_len == a, "find_option_end name");
  }
  return 0;
}
