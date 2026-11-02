// CBMC proofs for src/cjson/strbuf.c and the strbuf.h helpers, every input (strengthened
// after the independent review, ../REVIEW.md). Spec: strbuf.h / strbuf.c comments: size =
// bytes allocated to buf, length = string length without the NUL, length < size.
// Same properties as ../cbmc/harness.c, with these changes:
//  R1 model_review.h: free/realloc deallocate, so use-after-free is caught.
//  R2 empty strings: the "earlier byte k" check is conditional, so length == 0
//     is no longer assumed away (it was in free_to_string, append_string, helpers).
//  R3 no size <= 8 / size <= 16 bounds: buffers of any size up to 2^50, so a
//     32-bit truncation of a size or length is caught.
//  R4 strbuf_resize also with debug != 0 (its debug > 1 branch).
//  R5 strbuf_resize with the exact reallocs precondition, reallocs < INT_MAX.
//  R6 strbuf_allocated also on buf == NULL; strbuf_set_length for 0 <= len < size;
//     ensure_empty_length for every len with length + len + 1 <= SIZE_MAX.
#include "model.h"
#include STRBUF_C
#include <limits.h>

static size_t g_len;

static strbuf_t *any_strbuf(int dynamic) {
  strbuf_t *s = __CPROVER_allocate(sizeof(strbuf_t), 0);
  size_t size = nondet_size();
  __CPROVER_assume(1 <= size && size <= MAX_OBJ);
  s->buf = __CPROVER_allocate(size, 0);
  s->size = size;
  s->length = nondet_size();
  __CPROVER_assume(s->length < size);
  s->dynamic = dynamic;
  s->reallocs = nondet_int();
  __CPROVER_assume(s->reallocs >= 0 && s->reallocs < INT_MAX / 2);   // as ../cbmc; r_resize widens it
  s->debug = 0;
  return s;
}
// an index of an existing byte, if there is one
static size_t any_k(size_t L) { size_t k = nondet_size(); __CPROVER_assume(L == 0 ? k == 0 : k < L); return k; }

static bool init_may_die(void) { return g_len == SIZE_MAX || alloc_failed; }
static void check_init(strbuf_t *s, size_t len) {
  size_t want = len ? len + 1 : STRBUF_DEFAULT_SIZE;
  __CPROVER_assert(len != SIZE_MAX && !alloc_failed, "returns only when it could allocate");
  __CPROVER_assert(s->size == want && __CPROVER_OBJECT_SIZE(s->buf) == want && __CPROVER_POINTER_OFFSET(s->buf) == 0, "size");
  __CPROVER_assert(s->length == 0 && s->buf[0] == 0, "empty string");
  __CPROVER_assert(s->reallocs == 0 && s->debug == 0, "counters");
}
void h_init(void) {
  strbuf_t s; g_len = nondet_size(); die_ok = init_may_die;
  strbuf_init(&s, g_len);
  check_init(&s, g_len);
  __CPROVER_assert(s.dynamic == 0 && n_alloc == 1 && n_free == 0, "one allocation, not dynamic");
}
void h_new(void) {
  g_len = nondet_size(); die_ok = init_may_die;
  strbuf_t *s = strbuf_new(g_len);
  __CPROVER_assert(__CPROVER_OBJECT_SIZE(s) == sizeof(strbuf_t) && __CPROVER_POINTER_OFFSET(s) == 0, "fresh struct");
  check_init(s, g_len);
  __CPROVER_assert(s->dynamic == 1 && n_alloc == 2 && n_free == 0, "two allocations, dynamic");
  __CPROVER_assert(__CPROVER_same_object(s, s->buf) == 0, "separate blocks");
}
static bool never(void) { return false; }
void h_free(void) {
  int dyn = nondet_bool(); strbuf_t *s = any_strbuf(dyn); die_ok = never;
  s->debug = nondet_int();
  if (nondet_bool()) s->buf = NULL;
  char *b = s->buf;
  strbuf_free(s);
  __CPROVER_assert(n_free == (b != NULL) + dyn, "frees exactly buf and, if dynamic, s");
  if (b) __CPROVER_assert(was_freed(b), "buf freed");
  if (dyn) __CPROVER_assert(was_freed(s), "struct freed");
  else {
    __CPROVER_assert(s->buf == NULL, "buf cleared");
    int before = n_free; strbuf_free(s);
    __CPROVER_assert(n_free == before, "second free frees nothing");
  }
}
void h_free_to_string(void) {
  int dyn = nondet_bool(); strbuf_t *s = any_strbuf(dyn); die_ok = never;
  s->debug = nondet_int();
  size_t L = s->length; size_t k = any_k(L);
  char ck = s->buf[k]; char *b = s->buf;
  size_t out = 12345; size_t *lp = nondet_bool() ? &out : NULL;
  char *r = strbuf_free_to_string(s, lp);
  __CPROVER_assert(r == b && r[L] == 0, "same buffer, NUL at length");
  if (L) __CPROVER_assert(r[k] == ck, "string kept");
  if (lp) __CPROVER_assert(out == L, "*len = length"); else __CPROVER_assert(out == 12345, "len NULL: nothing written");
  __CPROVER_assert(n_free == dyn && (!dyn || was_freed(s)), "struct freed iff dynamic; buf not freed");
}
static bool cns_may_die(void) { return g_len == 0 || g_len == SIZE_MAX; }
static void check_new_size(size_t size, size_t len, size_t r) {
  size_t req = len + 1;
  __CPROVER_assert(len != 0 && len != SIZE_MAX, "returns only for 0 < len < SIZE_MAX");
  if (size > req) { __CPROVER_assert(r == req, "shrink exactly"); return; }
  if (req >= SIZE_MAX / 2) { __CPROVER_assert(r == req, "large: exact"); return; }
  __CPROVER_assert(r >= req, "big enough");
  int sh = __builtin_clzll(size) - __builtin_clzll(r);
  __CPROVER_assert(sh >= 0 && (size << sh) == r, "size times a power of two");
  __CPROVER_assert(r == size || (r >> 1) < req, "least such");
}
// calculate_new_size on every size >= 1 (it touches no buffer)
void h_calculate_new_size(void) {
  strbuf_t t; t.size = nondet_size(); __CPROVER_assume(t.size >= 1);
  t.debug = nondet_int();
  g_len = nondet_size(); die_ok = cns_may_die;
  size_t size = t.size;
  size_t r = calculate_new_size(&t, g_len);
  check_new_size(size, g_len, r);
  __CPROVER_assert(t.size == size, "s not changed");
}
static bool resize_may_die(void) { return g_len == 0 || g_len == SIZE_MAX || alloc_failed; }
void h_resize(void) {
  int dyn = nondet_bool();
  strbuf_t *s = any_strbuf(dyn); g_len = nondet_size(); die_ok = resize_may_die;
  s->debug = nondet_int();
  int dbg = s->debug;
  s->reallocs = nondet_int(); __CPROVER_assume(s->reallocs >= 0 && s->reallocs < INT_MAX);   // R5: exact
  size_t old = s->size, L = s->length; int ra = s->reallocs;
  size_t k = nondet_size(); __CPROVER_assume(k < old); char ck = s->buf[k];
  strbuf_resize(s, g_len);
  __CPROVER_assert(!alloc_failed, "returns only when realloc worked");
  check_new_size(old, g_len, s->size);
  __CPROVER_assert(__CPROVER_OBJECT_SIZE(s->buf) == s->size && __CPROVER_POINTER_OFFSET(s->buf) == 0, "block of the new size");
  if (k < s->size) __CPROVER_assert(s->buf[k] == ck, "contents kept");
  __CPROVER_assert(s->length == L && s->reallocs == ra + 1, "length kept, one more realloc");
  __CPROVER_assert(s->dynamic == dyn && s->debug == dbg && n_free == 0, "nothing else changed");
}
static bool always(void) { return true; }
void h_die(void) {
  die_ok = always;
  die("Overflow, len: %zu", nondet_size());
  __CPROVER_assert(0, "die returned");
}
void h_debug_stats(void) {
  strbuf_t *s = any_strbuf(nondet_bool()); die_ok = never;
  s->debug = nondet_int();
  strbuf_t before = *s;
  size_t k = nondet_size(); __CPROVER_assume(k < s->size); char ck = s->buf[k];
  debug_stats(s);
  __CPROVER_assert(s->buf == before.buf && s->size == before.size && s->length == before.length &&
                   s->dynamic == before.dynamic && s->reallocs == before.reallocs && s->debug == before.debug, "unchanged");
  __CPROVER_assert(s->buf[k] == ck, "buffer unchanged");
  __CPROVER_assert(n_alloc == 0 && n_free == 0, "no allocation");
}
#ifndef APPEND_MAX
#define APPEND_MAX 5
#endif
static bool append_may_die(void) { return alloc_failed; }
void h_append_string(void) {
  int dyn = nondet_bool();
  strbuf_t *s = any_strbuf(dyn); die_ok = append_may_die;
  size_t n = nondet_size(); __CPROVER_assume(n <= APPEND_MAX);
  char *str = __CPROVER_allocate(n + 1, 0);
  for (size_t i = 0; i < n; i++) __CPROVER_assume(str[i] != 0);
  str[n] = 0;
  size_t L = s->length; size_t k = any_k(L); char ck = s->buf[k];
  strbuf_append_string(s, str);
  __CPROVER_assert(s->length == L + n && s->length < s->size, "length grows by n, room for the NUL");
  __CPROVER_assert(__CPROVER_OBJECT_SIZE(s->buf) == s->size, "buf has size bytes");
  if (L) __CPROVER_assert(s->buf[k] == ck, "earlier bytes kept");
  for (size_t i = 0; i < n; i++) __CPROVER_assert(s->buf[L + i] == str[i], "bytes appended");
  __CPROVER_assert(s->dynamic == dyn && n_free == 0, "nothing else changed");
}
static bool helpers_may_die(void) { return alloc_failed; }
void h_helpers(void) {
  strbuf_t *s = any_strbuf(nondet_bool()); die_ok = helpers_may_die;
  size_t L = s->length, S = s->size; char *B = s->buf;
  size_t k = any_k(L); char ck = B[k];
  int which = nondet_int();
#ifdef WHICH
  __CPROVER_assume(which == WHICH);   // one helper per run (run_mutants.py)
#endif
  if (which == 0) { strbuf_reset(s); __CPROVER_assert(s->length == 0 && s->buf == B && s->size == S, "reset"); }
  else if (which == 1) { if (nondet_bool()) s->buf = NULL;
    __CPROVER_assert(strbuf_allocated(s) == (s->buf != NULL), "allocated"); }
  else if (which == 2) { __CPROVER_assert(strbuf_empty_length(s) == S - L - 1, "room left, NUL kept"); }
  else if (which == 3) { __CPROVER_assert(strbuf_empty_ptr(s) == B + L, "end of string"); }
  else if (which == 4) { __CPROVER_assert(strbuf_length(s) == L, "length"); }
  else if (which == 5) {
    size_t lp = 7; size_t *p = nondet_bool() ? &lp : NULL;
    __CPROVER_assert(strbuf_string(s, p) == B && (!p || lp == L) && (p || lp == 7), "string");
  } else if (which == 6) { strbuf_ensure_null(s); __CPROVER_assert(s->buf[L] == 0 && (!L || s->buf[k] == ck), "NUL at length"); }
  else if (which == 7) {
    size_t len = nondet_size(); __CPROVER_assume(len <= SIZE_MAX - L - 1);   // precondition: length + len + 1 fits
    strbuf_ensure_empty_length(s, len);
    __CPROVER_assert(s->size - s->length - 1 >= len && s->length == L && (!L || s->buf[k] == ck), "room");
    __CPROVER_assert(__CPROVER_OBJECT_SIZE(s->buf) == s->size, "size");
    if (len <= S - L - 1) __CPROVER_assert(s->buf == B && s->size == S, "no resize when room");
  } else if (which == 8) {
    char c = nondet_char(); strbuf_append_char(s, c);
    __CPROVER_assert(s->length == L + 1 && s->buf[L] == c && (!L || s->buf[k] == ck) && s->length < s->size, "append_char");
  } else if (which == 9) {
    __CPROVER_assume(L + 1 < S);
    char c = nondet_char(); strbuf_append_char_unsafe(s, c);
    __CPROVER_assert(s->length == L + 1 && s->buf[L] == c && (!L || s->buf[k] == ck), "append_char_unsafe");
  } else if (which == 10 || which == 11) {
    size_t n = nondet_size(); __CPROVER_assume(n <= 6);
    char *src = __CPROVER_allocate(n ? n : 1, 0);
    if (which == 11) __CPROVER_assume(L + n < S);
    if (which == 10) strbuf_append_mem(s, src, n); else strbuf_append_mem_unsafe(s, src, n);
    __CPROVER_assert(s->length == L + n && s->length < s->size && (!L || s->buf[k] == ck), "append_mem length");
    for (size_t i = 0; i < n; i++) __CPROVER_assert(s->buf[L + i] == src[i], "append_mem bytes");
  } else if (which == 12) {
    size_t n = nondet_size(); __CPROVER_assume(L + n < S);
    strbuf_extend_length(s, n); __CPROVER_assert(s->length == L + n, "extend");
  } else if (which == 13) {   // set_length on its safe domain (negative len stays OPEN)
    int len = nondet_int(); __CPROVER_assume(len >= 0 && (size_t)len < S);
    strbuf_set_length(s, len); __CPROVER_assert(s->length == (size_t)len && s->buf == B && s->size == S, "set_length");
  }
}
