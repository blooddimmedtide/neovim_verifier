// registerdigraph: after registering (c1,c2)->n with n != 0, looking up (c1,c2) gives n,
// and the table holds exactly one entry for the pair. Run with -DFIXED for the fixed code.
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#define NUL '\000'
#define ESC '\033'
#define IS_SPECIAL(c) ((c) < 0)
#define N_(s) s
#define _(s) s
#define MB_MAXCHAR 6
typedef int result_T;
#ifdef FIXED
typedef struct { int char1; int char2; result_T result; } digr_T;
#else
typedef struct { uint8_t char1; uint8_t char2; result_T result; } digr_T;
#endif
typedef struct { int ga_len; int ga_maxlen; int ga_itemsize; int ga_growsize; void *ga_data; } garray_T;
static const char e_digraph_must_be_just_two_characters_str[] = "E1214";
static garray_T user_digraphs;
int nondet_int(void); uint8_t nondet_u8(void); char nondet_char(void);
static void semsg(const char *f, const char *a) { (void)f; (void)a; }
static void emsg(const char *f) { (void)f; }
static int utf_char2bytes(int c, char *buf) { (void)c; buf[0] = 'x'; return 1; }
// Garray append model (not the garray proof's stub): the table lives in a buffer with exactly
// one free slot; append asserts the slot is free, zeroes it and bumps ga_len. This is
// ga_append_via_ptr's documented effect; growth and allocation failure are not modelled.
static digr_T *slot_buf; static int slot_cap;
static void *ga_append_via_ptr(garray_T *gap, size_t sz) {
  assert(sz == sizeof(digr_T) && gap->ga_data == slot_buf && gap->ga_len < slot_cap);
  digr_T *d = &slot_buf[gap->ga_len++]; d->char1 = 0; d->char2 = 0; d->result = 0; return d;
}
#define GA_APPEND_VIA_PTR(item_type, gap) ga_append_via_ptr(gap, sizeof(item_type))
#ifdef FIXED
#include "extracted_register_fixed.c"
#else
#include "extracted_register.c"
#endif
#ifndef NU
#define NU 2
#endif
void check_register(void) {
  int n0 = nondet_int(); __CPROVER_assume(n0 >= 0 && n0 <= NU);
  digr_T *p = malloc(sizeof(digr_T) * (size_t)(n0 + 1)); __CPROVER_assume(p != NULL); slot_buf = p; slot_cap = n0 + 1;
#ifdef FIXED
  for (int i = 0; i < n0; i++) { p[i].char1 = nondet_int(); p[i].char2 = nondet_int(); p[i].result = nondet_int(); }
#else
  for (int i = 0; i < n0; i++) { p[i].char1 = nondet_u8(); p[i].char2 = nondet_u8(); p[i].result = nondet_int(); }
#endif
  // the table has no duplicate pairs (invariant kept by registerdigraph itself)
  for (int i = 0; i < n0; i++) for (int j = i + 1; j < n0; j++)
    __CPROVER_assume(!(p[i].char1 == p[j].char1 && p[i].char2 == p[j].char2));
  user_digraphs.ga_len = n0; user_digraphs.ga_data = p; user_digraphs.ga_itemsize = sizeof(digr_T);
  // inputs as digraph_set() passes them: any accepted codepoint pair (check_digraph_chars_valid)
  int c1 = nondet_int(), c2 = nondet_int(), n = nondet_int();
  __CPROVER_assume(c1 > 0 && c1 <= 0x10FFFF && c2 > 0 && c2 <= 0x10FFFF && n != 0);
  __CPROVER_assume(check_digraph_chars_valid(c1, c2));
  registerdigraph(c1, c2, n);
  const digr_T *u = user_digraphs.ga_data; int found = 0, cnt = 0;
  for (int i = 0; i < user_digraphs.ga_len; i++)
    if (u[i].char1 == c1 && u[i].char2 == c2) { cnt++; found = u[i].result; }
  assert(cnt == 1 && found == n);   // the user digraph {c1}{c2} now yields n
}
