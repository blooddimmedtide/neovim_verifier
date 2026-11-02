// CBMC proofs for src/cjson/strbuf.c (and the strbuf.h helpers), every input.
// The spec comes from the comments in strbuf.h / strbuf.c: size = bytes
// allocated to buf, length = string length without the optional NUL, so a
// strbuf in use satisfies length < size and buf has size bytes (strbuf.h:
// "Ensure there is space for a NULL terminator").
#include "model.h"
#include STRBUF_C   // verbatim src/cjson/strbuf.c (it includes strbuf.h)

static size_t g_len;
static strbuf_t *g_s;

// A strbuf in use, as strbuf_init / strbuf_resize leave it.
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
  __CPROVER_assume(s->reallocs >= 0 && s->reallocs < INT32_MAX / 2);   // see CLAIM.md: a counter of resizes
  s->debug = 0;   // debug output is off unless a caller sets it (lua_cjson never does)
  return s;
}

// strbuf_init: size is len + 1 (1023 for len 0), buf is a fresh block of that
// size holding "", all counters 0. Dies only when len + 1 overflows or malloc fails.
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
// strbuf_new: a fresh strbuf_t holding an initialised buffer, marked dynamic.
void h_new(void) {
  g_len = nondet_size(); die_ok = init_may_die;
  strbuf_t *s = strbuf_new(g_len);
  __CPROVER_assert(__CPROVER_OBJECT_SIZE(s) == sizeof(strbuf_t) && __CPROVER_POINTER_OFFSET(s) == 0, "fresh struct");
  check_init(s, g_len);
  __CPROVER_assert(s->dynamic == 1 && n_alloc == 2 && n_free == 0, "two allocations, dynamic");
  __CPROVER_assert(__CPROVER_same_object(s, s->buf) == 0, "separate blocks");
}
static bool never(void) { return false; }
// strbuf_free: frees buf (if any) and, when dynamic, the struct; a non-dynamic
// strbuf is left with buf == NULL, so freeing it again frees nothing.
void h_free(void) {
  int dyn = nondet_bool(); strbuf_t *s = any_strbuf(dyn); die_ok = never;
  if (nondet_bool()) s->buf = NULL;   // already freed once
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
// strbuf_free_to_string: returns buf holding the string, NUL-terminated, sets
// *len to its length when len is not NULL, frees the struct when dynamic.
void h_free_to_string(void) {
  int dyn = nondet_bool(); strbuf_t *s = any_strbuf(dyn); die_ok = never;
  size_t k = nondet_size(); __CPROVER_assume(k < s->length);
  char ck = s->buf[k]; size_t L = s->length; char *b = s->buf;
  size_t out = 12345; size_t *lp = nondet_bool() ? &out : NULL;
  char *r = strbuf_free_to_string(s, lp);
  __CPROVER_assert(r == b && r[L] == 0 && r[k] == ck, "same buffer, string kept, NUL at length");
  if (lp) __CPROVER_assert(out == L, "*len = length"); else __CPROVER_assert(out == 12345, "len NULL: nothing written");
  __CPROVER_assert(n_free == dyn && (!dyn || was_freed(s)), "struct freed iff dynamic; buf not freed");
}

// calculate_new_size(s, len): reqsize = len + 1. Dies when len is 0 or len + 1
// overflows. Shrinks exactly (returns reqsize) when size > reqsize. Otherwise
// returns reqsize when reqsize >= SIZE_MAX / 2, else the smallest size * 2^k >= reqsize.
static bool cns_may_die(void) { return g_len == 0 || g_len == SIZE_MAX; }
static void check_new_size(size_t size, size_t len, size_t r) {
  size_t req = len + 1;
  __CPROVER_assert(len != 0 && len != SIZE_MAX, "returns only for 0 < len < SIZE_MAX");
  if (size > req) { __CPROVER_assert(r == req, "shrink exactly"); return; }
  if (req >= SIZE_MAX / 2) { __CPROVER_assert(r == req, "large: exact"); return; }
  // r = size * 2^k for the least k with r >= req
  __CPROVER_assert(r >= req, "big enough");
  int sh = __builtin_clzll(size) - __builtin_clzll(r);
  __CPROVER_assert(sh >= 0 && (size << sh) == r, "size times a power of two");
  __CPROVER_assert(r == size || (r >> 1) < req, "least such");
}
void h_calculate_new_size(void) {
  strbuf_t *s = any_strbuf(0); g_len = nondet_size(); die_ok = cns_may_die;
  size_t size = s->size;
  size_t r = calculate_new_size(s, g_len);
  check_new_size(size, g_len, r);
}
// strbuf_resize(s, len): size becomes calculate_new_size(s, len), buf a block
// of exactly that size keeping the first min(old size, new size) bytes;
// reallocs grows by one. Dies on a bad len or when realloc fails.
static bool resize_may_die(void) { return g_len == 0 || g_len == SIZE_MAX || alloc_failed; }
void h_resize(void) {
  strbuf_t *s = any_strbuf(nondet_bool()); g_len = nondet_size(); die_ok = resize_may_die; g_s = s;
  size_t old = s->size, L = s->length; int ra = s->reallocs;
  size_t k = nondet_size(); __CPROVER_assume(k < old); char ck = s->buf[k];
  strbuf_resize(s, g_len);
  __CPROVER_assert(!alloc_failed, "returns only when realloc worked");
  check_new_size(old, g_len, s->size);
  __CPROVER_assert(__CPROVER_OBJECT_SIZE(s->buf) == s->size && __CPROVER_POINTER_OFFSET(s->buf) == 0, "block of the new size");
  if (k < s->size) __CPROVER_assert(s->buf[k] == ck, "contents kept");
  __CPROVER_assert(s->length == L && s->reallocs == ra + 1, "length kept, one more realloc");
}
static bool always(void) { return true; }
// die: prints the message and aborts; it never returns.
void h_die(void) {
  die_ok = always;
  die("Overflow, len: %zu", nondet_size());
  __CPROVER_assert(0, "die returned");
}
// debug_stats: prints statistics when debug is set; changes nothing either way.
void h_debug_stats(void) {
  strbuf_t *s = any_strbuf(nondet_bool()); die_ok = never;
  s->debug = nondet_int();
  strbuf_t before = *s;
  debug_stats(s);
  __CPROVER_assert(s->buf == before.buf && s->size == before.size && s->length == before.length &&
                   s->dynamic == before.dynamic && s->reallocs == before.reallocs && s->debug == before.debug, "unchanged");
  __CPROVER_assert(n_alloc == 0 && n_free == 0, "no allocation");
}
// strbuf_append_string for strings of length 0..APPEND_MAX (exact objects, so a
// read past the NUL fails): the bytes of str are appended, earlier bytes kept,
// the strbuf stays in use. The unbounded proof is in ../wp.
#ifndef APPEND_MAX
#define APPEND_MAX 5
#endif
static bool append_may_die(void) { return alloc_failed; }
void h_append_string(void) {
  strbuf_t *s = any_strbuf(nondet_bool()); die_ok = append_may_die;
  __CPROVER_assume(s->size <= 8);   // small buffers so that resizing happens
  size_t n = nondet_size(); __CPROVER_assume(n <= APPEND_MAX);
  char *str = __CPROVER_allocate(n + 1, 0);
  for (size_t i = 0; i < n; i++) __CPROVER_assume(str[i] != 0);
  str[n] = 0;
  size_t L = s->length; size_t k = nondet_size(); __CPROVER_assume(k < L); char ck = s->buf[k];
  strbuf_append_string(s, str);
  __CPROVER_assert(s->length == L + n && s->length < s->size, "length grows by n, room for the NUL");
  __CPROVER_assert(__CPROVER_OBJECT_SIZE(s->buf) == s->size, "buf has size bytes");
  __CPROVER_assert(s->buf[k] == ck, "earlier bytes kept");
  for (size_t i = 0; i < n; i++) __CPROVER_assert(s->buf[L + i] == str[i], "bytes appended");
}
// The strbuf.h helpers used by strbuf.c and lua_cjson.c, on a strbuf in use.
static bool helpers_may_die(void) { return alloc_failed; }
void h_helpers(void) {
  strbuf_t *s = any_strbuf(nondet_bool()); die_ok = helpers_may_die;
  __CPROVER_assume(s->size <= 16);
  size_t L = s->length, S = s->size; char *B = s->buf;
  size_t k = nondet_size(); __CPROVER_assume(k < L); char ck = B[k];
  int which = nondet_int();
  if (which == 0) { strbuf_reset(s); __CPROVER_assert(s->length == 0 && s->buf == B && s->size == S, "reset"); }
  else if (which == 1) { __CPROVER_assert(strbuf_allocated(s) == (s->buf != NULL), "allocated"); }
  else if (which == 2) { __CPROVER_assert(strbuf_empty_length(s) == S - L - 1, "room left, NUL kept"); }
  else if (which == 3) { __CPROVER_assert(strbuf_empty_ptr(s) == B + L, "end of string"); }
  else if (which == 4) { __CPROVER_assert(strbuf_length(s) == L, "length"); }
  else if (which == 5) {
    size_t lp = 7; size_t *p = nondet_bool() ? &lp : NULL;
    __CPROVER_assert(strbuf_string(s, p) == B && (!p || lp == L) && (p || lp == 7), "string");
  } else if (which == 6) { strbuf_ensure_null(s); __CPROVER_assert(s->buf[L] == 0 && s->buf[k] == ck, "NUL at length"); }
  else if (which == 7) {   // ensure_empty_length: afterwards at least len bytes of room
    size_t len = nondet_size(); __CPROVER_assume(len <= 16);
    strbuf_ensure_empty_length(s, len);
    __CPROVER_assert(s->size - s->length - 1 >= len && s->length == L && s->buf[k] == ck, "room");
    __CPROVER_assert(__CPROVER_OBJECT_SIZE(s->buf) == s->size, "size");
    if (len <= S - L - 1) __CPROVER_assert(s->buf == B && s->size == S, "no resize when room");
  } else if (which == 8) {
    char c = nondet_char(); strbuf_append_char(s, c);
    __CPROVER_assert(s->length == L + 1 && s->buf[L] == c && s->buf[k] == ck && s->length < s->size, "append_char");
  } else if (which == 9) {   // the _unsafe variant needs one byte of room (its name says so)
    __CPROVER_assume(L + 1 < S);
    char c = nondet_char(); strbuf_append_char_unsafe(s, c);
    __CPROVER_assert(s->length == L + 1 && s->buf[L] == c && s->buf[k] == ck, "append_char_unsafe");
  } else if (which == 10 || which == 11) {
    size_t n = nondet_size(); __CPROVER_assume(n <= 6);
    char *src = __CPROVER_allocate(n ? n : 1, 0);
    if (which == 11) __CPROVER_assume(L + n < S);   // _unsafe: room for n
    if (which == 10) strbuf_append_mem(s, src, n); else strbuf_append_mem_unsafe(s, src, n);
    __CPROVER_assert(s->length == L + n && s->length < s->size && s->buf[k] == ck, "append_mem length");
    for (size_t i = 0; i < n; i++) __CPROVER_assert(s->buf[L + i] == src[i], "append_mem bytes");
  } else if (which == 12) {   // extend_length: the caller wrote n bytes at empty_ptr
    size_t n = nondet_size(); __CPROVER_assume(L + n < S);
    strbuf_extend_length(s, n); __CPROVER_assert(s->length == L + n, "extend");
  }
}
