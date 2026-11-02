// Reviewer probes for ../cbmc/harness.c (independent review, see ../REVIEW.md).
// Built exactly like the harnesses (same model.h, same STRBUF_C), run by probes.sh.
//  c_*  : __CPROVER_cover goals, run with --cover cover. A goal reported FAILED
//         means the situation is NOT reachable under the harness's assumptions.
//  q_*  : precondition / model probes, run as ordinary proofs. The expected
//         verdict is in probes.sh.
#include "../cbmc/harness.c"
#include <limits.h>

// --- the setups of the existing harnesses, copied literally, plus covers ---
void c_free_to_string(void) {   // h_free_to_string setup
  int dyn = nondet_bool(); strbuf_t *s = any_strbuf(dyn); die_ok = never;
  size_t k = nondet_size(); __CPROVER_assume(k < s->length);
  __CPROVER_cover(s->length == 0);            // empty string
  __CPROVER_cover(s->length == s->size - 1);  // full buffer
}
void c_append_string(void) {    // h_append_string setup
  strbuf_t *s = any_strbuf(nondet_bool()); die_ok = append_may_die;
  __CPROVER_assume(s->size <= 8);
  size_t n = nondet_size(); __CPROVER_assume(n <= APPEND_MAX);
  char *str = __CPROVER_allocate(n + 1, 0);
  for (size_t i = 0; i < n; i++) __CPROVER_assume(str[i] != 0);
  str[n] = 0;
  size_t L = s->length; size_t k = nondet_size(); __CPROVER_assume(k < L);
  int ra = s->reallocs;
  __CPROVER_cover(L == 0);                    // append to an empty strbuf
  strbuf_append_string(s, str);
  __CPROVER_cover(s->reallocs == ra + 1);
  __CPROVER_cover(s->reallocs == ra + 2);     // two resizes in one call
  __CPROVER_cover(s->size > 8);
}
void c_helpers(void) {          // h_helpers setup
  strbuf_t *s = any_strbuf(nondet_bool()); die_ok = helpers_may_die;
  __CPROVER_assume(s->size <= 16);
  size_t L = s->length; size_t k = nondet_size(); __CPROVER_assume(k < L);
  __CPROVER_cover(L == 0);                    // helpers on an empty strbuf
  __CPROVER_cover(s->buf == NULL);            // strbuf_allocated() == 0
  __CPROVER_cover(s->size - L - 1 > 0xffffffffu);   // room that does not fit 32 bits
}
void c_resize(void) {           // h_resize setup
  strbuf_t *s = any_strbuf(nondet_bool()); g_len = nondet_size(); die_ok = resize_may_die;
  size_t old = s->size;
  __CPROVER_cover(s->debug > 1);              // the debug branch of strbuf_resize
  strbuf_resize(s, g_len);
  __CPROVER_cover(s->size < old);
  __CPROVER_cover(s->size > old);
  __CPROVER_cover(s->size == old);
  __CPROVER_cover(g_len + 1 >= SIZE_MAX / 2); // the "large: exact" branch, after success
}
void c_cns(void) {              // h_calculate_new_size setup
  strbuf_t *s = any_strbuf(0); g_len = nondet_size(); die_ok = cns_may_die;
  size_t size = s->size;
  __CPROVER_cover(size > MAX_OBJ);            // a size above the model's 2^50
  size_t r = calculate_new_size(s, g_len);
  __CPROVER_cover(size < g_len + 1 && g_len + 1 < SIZE_MAX / 2 && r >= 4 * size); // >= 2 doublings
  __CPROVER_cover(g_len + 1 >= SIZE_MAX / 2 && size <= g_len + 1);
}
void c_init(void) {
  strbuf_t s; g_len = nondet_size(); die_ok = init_may_die;
  strbuf_init(&s, g_len);
  __CPROVER_cover(g_len > MAX_OBJ);           // returns for a len above 2^50 (never: model)
  __CPROVER_cover(g_len == 0);
}

// --- q_*: preconditions and model ---
// q_reallocs_max: a strbuf whose reallocs is INT_MAX. Expected FAILED (signed
// overflow in reallocs++), so the harness precondition reallocs < INT_MAX/2 is a
// real restriction on strbuf_resize, not a vacuous one.
void q_reallocs_max(void) {
  strbuf_t *s = any_strbuf(0); s->reallocs = INT_MAX; g_len = nondet_size(); die_ok = resize_may_die;
  strbuf_resize(s, g_len);
}
// q_resize_no_growth: strbuf_resize to the current capacity grows nothing but
// still counts a realloc, so reallocs is not bounded by the number of growths
// (CLAIM.md's justification). Expected SUCCESS (the property holds).
void q_resize_no_growth(void) {
  strbuf_t *s = any_strbuf(0); g_len = s->size - 1; die_ok = resize_may_die;
  __CPROVER_assume(g_len > 0);
  size_t old = s->size; int ra = s->reallocs;
  strbuf_resize(s, g_len);
  __CPROVER_assert(s->size == old && s->reallocs == ra + 1, "same size, one more realloc");
}
// q_ensure_wrap: strbuf_ensure_empty_length with s->length + len wrapping.
// Expected FAILED: the room postcondition (or die_ok) breaks, so the helper has
// the precondition len <= SIZE_MAX - length - 1, which CLAIM.md does not list.
void q_ensure_wrap(void) {
  strbuf_t *s = any_strbuf(0); die_ok = helpers_may_die;
  __CPROVER_assume(s->size <= 16);
  size_t len = nondet_size();
  strbuf_ensure_empty_length(s, len);
  __CPROVER_assert(s->size - s->length - 1 >= len, "room");
}
// q_uaf_unseen: the model's free() only records the pointer, so a read after
// free is not a --pointer-check failure. Expected SUCCESS (that is the gap).
void q_uaf_unseen(void) {
  strbuf_t *s = malloc(sizeof(strbuf_t)); __CPROVER_assume(s != NULL);
  s->length = 3; free(s);
  __CPROVER_assert(s->length == 3, "read after free passes");
}
// q_realloc_stale: realloc does not end the old block's lifetime in the model,
// so code that keeps using the old pointer is not caught. Expected SUCCESS (gap).
void q_realloc_stale(void) {
  char *p = malloc(4); __CPROVER_assume(p != NULL);
  char *q = realloc(p, 8); __CPROVER_assume(q != NULL);
  p[0] = 1;   // stale pointer write
}
// q_cns_wide: calculate_new_size on every size >= 1 (no buffer needed),
// beyond any_strbuf's 2^50. Expected SUCCESS (the claim extends).
void q_cns_wide(void) {
  strbuf_t t; t.size = nondet_size(); __CPROVER_assume(t.size >= 1);
  g_len = nondet_size(); die_ok = cns_may_die;
  size_t size = t.size;
  size_t r = calculate_new_size(&t, g_len);
  check_new_size(size, g_len, r);
}
