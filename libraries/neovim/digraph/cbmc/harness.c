#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <assert.h>
#define NUL '\000'
#define ESC '\033'
#define OK 1
#define FAIL 0
#define IS_SPECIAL(c) ((c) < 0)
#define N_(s) s
#define _(s) s
#define MB_MAXCHAR 6
typedef int result_T;
typedef struct { uint8_t char1; uint8_t char2; result_T result; } digr_T;
typedef struct { int ga_len; int ga_maxlen; int ga_itemsize; int ga_growsize; void *ga_data; } garray_T;
static const char e_digraph_must_be_just_two_characters_str[] = "E1214";
static garray_T user_digraphs;
int nondet_int(void); _Bool nondet_bool(void); uint8_t nondet_u8(void); char nondet_char(void);
static int emsg_count;
// stubs for message output: no effect on the result, only counted.
static void semsg(const char *f, const char *a) { (void)f; (void)a; emsg_count++; }
static void emsg(const char *f) { (void)f; emsg_count++; }
// utf_char2bytes contract stub (proved for all ints in libraries/neovim/mbyte): writes 1..4 bytes.
static int utf_char2bytes(int c, char *buf) { (void)c; int n = nondet_int();
  __CPROVER_assume(n >= 1 && n <= 4); for (int i = 0; i < n; i++) buf[i] = nondet_char(); return n; }
#include "extracted.c"
#include "spec.h"
#ifndef NU
#define NU 3
#endif
static int nd(void) { int n = 0; while (digraphdefault[n].char1 != 0) n++; return n; }
static void setup_user(void) {
  int n = nondet_int(); __CPROVER_assume(n >= 0 && n <= NU);
  digr_T *p = n ? malloc(sizeof(digr_T) * (size_t)n) : NULL;   // exact size
  for (int i = 0; i < n; i++) { p[i].char1 = nondet_u8(); p[i].char2 = nondet_u8(); p[i].result = nondet_int(); }
  user_digraphs.ga_len = n; user_digraphs.ga_data = p; user_digraphs.ga_itemsize = sizeof(digr_T);
}
void check_exact(void) {
  setup_user();
  int c1 = nondet_int(), c2 = nondet_int(); bool meta = nondet_bool();
  int r = getexactdigraph(c1, c2, meta);
  assert(r == ref_exact(user_digraphs.ga_data, user_digraphs.ga_len, digraphdefault, nd(), c1, c2, meta));
}
void check_get(void) {
  setup_user();
  int c1 = nondet_int(), c2 = nondet_int(); bool meta = nondet_bool();
  const digr_T *u = user_digraphs.ga_data; int nu = user_digraphs.ga_len, n = nd();
  int r = digraph_get(c1, c2, meta);
  int fwd = ref_exact(u, nu, digraphdefault, n, c1, c2, meta);
  int rev = ref_exact(u, nu, digraphdefault, n, c2, c1, meta);
  // documented: forward pair if it is a digraph, else the reversed pair, else char2 (or meta)
  int want = (fwd != c2 || c1 == c2) ? fwd : (rev != c1 ? rev : c2);
  assert(r == want);
}
void check_valid(void) {
  int c1 = nondet_int(), c2 = nondet_int(); emsg_count = 0;
  bool v = check_digraph_chars_valid(c1, c2);
  assert(v == (c2 != 0 && c1 != ESC && c2 != ESC));
  assert(v ? emsg_count == 0 : emsg_count == 1);  // exactly one error message on rejection
}
