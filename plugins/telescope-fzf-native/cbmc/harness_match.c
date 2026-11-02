// CBMC: the six match algorithms of fzf.c against spec.h, for every text of
// length 0..NB and every pattern of length 0..MB (all byte values, NUL too),
// both case modes, normalize on/off, pos NULL or a position array of any
// capacity/fill up to PB, slab NULL or a slab of any capacity with arbitrary
// (stale) contents. Text and pattern are objects of exactly their length, so
// the pointer check proves nothing outside them is read.
#include <stdlib.h>
#include <string.h>
#ifndef NB
#define NB 5
#endif
#ifndef MB
#define MB 3
#endif
#define RV2_N NB
#define RV2_M MB
#include "spec.h"
#include "harness_util.h"
#ifdef FZFV_CODE_MALLOC
#define malloc fzfv_code_malloc   // see harness_util.h
#endif
#include FZF_C
#undef malloc

#ifndef NB
#define NB 5
#endif
#ifndef MB
#define MB 3
#endif
#define PB 2
#define SB16 (3 * NB + 2 * NB * MB + 1)
#define SB32 (MB + NB + 1)
#ifndef SC16
#define SC16 4
#endif
#define SC32 4

size_t nondet_size(void);
bool nondet_bool(void);
#define U(p) ((const unsigned char *)(p))

typedef struct {
  fzf_position_t *p;
  uint32_t old[PB];
  size_t os;
} posrec;

// pos: NULL, or an array holding 0..PB earlier positions with room for this
// call's positions. (The growing path of resize_pos / realloc is proved by
// h_append_pos and h_insert_range for every capacity up to their bound; inside
// the algorithm harnesses a realloc of symbolic size runs CBMC out of memory.)
static void any_pos(posrec *r) {
  r->p = NULL;
  if (nondet_bool()) return;
  fzf_position_t *p = malloc(sizeof *p);
  p->cap = PB + MB + 1;
  p->size = nondet_size();
  __CPROVER_assume(p->size <= PB);
  p->data = malloc((PB + MB + 1) * sizeof(uint32_t));
  for (size_t i = 0; i < p->size; i++) r->old[i] = p->data[i];
  r->os = p->size;
  r->p = p;
}
// pos must now hold its old entries followed by want[0..k-1].
static void check_pos(posrec *r, const size_t *want, size_t k) {
  if (!r->p) return;
  fzf_position_t *p = r->p;
  __CPROVER_assert(p->size == r->os + k, "positions: count");
  __CPROVER_assert(p->size <= p->cap && (p->cap == 0 || __CPROVER_OBJECT_SIZE(p->data) >= p->cap * sizeof(uint32_t)), "positions: capacity real");
  for (size_t i = 0; i < r->os; i++) __CPROVER_assert(p->data[i] == r->old[i], "positions: old kept");
  for (size_t i = 0; i < k; i++) __CPROVER_assert(p->data[r->os + i] == want[i], "positions: new");
}
// A slab big enough for every buffer v2 takes for text <= NB and pattern <=
// MB (3N + 2N*M int16, M + N int32), with arbitrary contents left by earlier
// calls; or the same with zeros (what a fresh slab or a NULL slab gives).
static fzf_slab_t *big_slab(bool zero) {
  fzf_slab_t *s = malloc(sizeof *s);
  s->I16.cap = SB16; s->I32.cap = SB32;
  s->I16.data = malloc(SB16 * sizeof(int16_t));
  s->I32.data = malloc(SB32 * sizeof(int32_t));
  if (zero) {
    for (size_t i = 0; i < SB16; i++) s->I16.data[i] = 0;
    for (size_t i = 0; i < SB32; i++) s->I32.data[i] = 0;
  }
  s->I16.size = s->I32.size = 0;
  s->I16.allocated = s->I32.allocated = true;
  return s;
}
// A slab of any capacity 0..SC16 / 0..SC32 with arbitrary contents.
static fzf_slab_t *small_slab(void) {
  fzf_slab_t *s = malloc(sizeof *s);
  s->I16.cap = nondet_size(); s->I32.cap = nondet_size();
  s->I16.data = exact_malloc(s->I16.cap, SC16, sizeof(int16_t));
  s->I32.data = exact_malloc(s->I32.cap, SC32, sizeof(int32_t));
  s->I16.size = s->I32.size = 0;
  s->I16.allocated = s->I32.allocated = true;
  return s;
}
// The five non-v2 algorithms ignore the slab argument.
static fzf_slab_t *any_slab(void) { return nondet_bool() ? NULL : small_slab(); }

typedef struct {
  char *t, *p;
  size_t n, m;
  bool cs, norm;
  fzf_string_t text, pat;
  posrec pr;
  fzf_slab_t *slab;
} setup;
static void any_setup(setup *s) {
  s->n = nondet_size(); s->m = nondet_size();
  __CPROVER_assume(s->n <= NB && s->m <= MB);
  s->t = exact_malloc(s->n, NB, 1); s->p = exact_malloc(s->m, MB, 1);
  s->cs = nondet_bool(); s->norm = nondet_bool();
  s->text = (fzf_string_t){s->t, s->n};
  s->pat = (fzf_string_t){s->p, s->m};
  any_pos(&s->pr);
  s->slab = any_slab();
}
static void check_res(fzf_result_t r, r_result w) {
  __CPROVER_assert(r.start == w.start && r.end == w.end, "start/end");
  __CPROVER_assert(r.score == w.score, "score");
}

// references: spec.h (ref_prefix, ref_suffix, ref_equal, ref_exact, ref_v1)

#define FUNCTIONAL(name, fn, ref)                                              \
  void name(void) {                                                            \
    setup s; any_setup(&s);                                                    \
    size_t want[MB + 1]; size_t k;                                             \
    r_result w = ref(U(s.t), s.n, U(s.p), s.m, s.cs, want, &k);                \
    fzf_result_t r = fn(s.cs, s.norm, &s.text, &s.pat, s.pr.p, s.slab);        \
    check_res(r, w);                                                           \
    check_pos(&s.pr, want, k);                                                 \
  }
FUNCTIONAL(h_prefix, fzf_prefix_match, ref_prefix)
FUNCTIONAL(h_suffix, fzf_suffix_match, ref_suffix)
FUNCTIONAL(h_equal, fzf_equal_match, ref_equal)
FUNCTIONAL(h_exact, fzf_exact_match_naive, ref_exact)
FUNCTIONAL(h_v1, fzf_fuzzy_match_v1, ref_v1)

// calculate_score alone on every window whose leftmost occurrence of the
// pattern ends at its last char (the windows every caller passes).
void h_calculate_score(void) {
  setup s; any_setup(&s);
  size_t a = nondet_size(), e = nondet_size();
  __CPROVER_assume(a <= e && e <= s.n && s.m >= 1);
  size_t want[MB];
  // leftmost occurrence inside [a, e) exists and ends at e - 1
  __CPROVER_assume(r_subseq(U(s.t), a, e, U(s.p), s.m, s.cs) && !r_subseq(U(s.t), a, e - 1, U(s.p), s.m, s.cs));
  int32_t w = r_score(U(s.t), a, e, U(s.p), s.m, s.cs, want);
  int32_t r = calculate_score(s.cs, s.norm, &s.text, &s.pat, a, e, s.pr.p);
  __CPROVER_assert(r == w, "calculate_score = fzf calculateScore");
  check_pos(&s.pr, want, s.m);
}

// FuzzyMatchV2 (fzf's modified Smith-Waterman). Proved: no UB / no access
// outside any object; the result is a match exactly when the pattern is a
// subsequence of the folded text; on a match the positions (appended last to
// first) are strictly decreasing, inside the text, each on a byte that folds
// to its pattern byte, and start/end are the first position and one past the
// last; for a 1-byte pattern the full result (best-bonus occurrence, earliest
// among ties). Three harnesses: h_v2 (big slab with stale contents: every
// buffer from the slab), h_v2_noslab (NULL slab: every buffer malloc'd),
// h_v2_fallback (slab smaller than N*M: exactly FuzzyMatchV1's result).
static void v2_props(setup *s, fzf_result_t r) {
  size_t want[MB + 1];
  if (s->m == 0) { check_res(r, (r_result){0, 0, 0}); check_pos(&s->pr, want, 0); return; }
  bool sub = r_subseq(U(s->t), 0, s->n, U(s->p), s->m, s->cs);
  if (!sub) { check_res(r, R_NOMATCH); check_pos(&s->pr, want, 0); return; }
  __CPROVER_assert(0 <= r.start && r.start < r.end && (size_t)r.end <= s->n, "range");
  __CPROVER_assert(r.score >= R_MATCH, "score at least one match");
  if (s->m == 1) {
    size_t best = s->n; int bb = -1;
    for (size_t i = 0; i < s->n; i++)
      if (r_fold(U(s->t)[i], s->cs) == U(s->p)[0] && r_bonus_at(U(s->t), i) > bb) { best = i; bb = r_bonus_at(U(s->t), i); }
    want[0] = best;
    check_res(r, (r_result){(int32_t)best, (int32_t)best + 1, R_MATCH + 2 * bb});
    check_pos(&s->pr, want, 1);
    return;
  }
  if (!s->pr.p) return;
  fzf_position_t *p = s->pr.p;
  __CPROVER_assert(p->size == s->pr.os + s->m, "m positions appended");
  for (size_t i = 0; i < s->pr.os; i++) __CPROVER_assert(p->data[i] == s->pr.old[i], "old kept");
  for (size_t q = 0; q < s->m; q++) {
    uint32_t x = p->data[s->pr.os + q];          // q-th appended = pattern byte m-1-q
    __CPROVER_assert(x < s->n, "position in text");
    __CPROVER_assert(r_fold(U(s->t)[x], s->cs) == U(s->p)[s->m - 1 - q], "position matches its pattern byte");
    if (q > 0) __CPROVER_assert(x < p->data[s->pr.os + q - 1], "strictly decreasing");
  }
  __CPROVER_assert((uint32_t)r.start == p->data[s->pr.os + s->m - 1], "start = first position");
  __CPROVER_assert((uint32_t)r.end == p->data[s->pr.os] + 1, "end = last position + 1");
}
void h_v2(void) {
  setup s; any_setup(&s);
  s.slab = big_slab(false);
  v2_props(&s, fzf_fuzzy_match_v2(s.cs, s.norm, &s.text, &s.pat, s.pr.p, s.slab));
}
void h_v2_noslab(void) {
  setup s; any_setup(&s);
  v2_props(&s, fzf_fuzzy_match_v2(s.cs, s.norm, &s.text, &s.pat, s.pr.p, NULL));
}
void h_v2_fallback(void) {
  setup s; any_setup(&s);
  s.slab = small_slab();
  __CPROVER_assume(s.n * s.m > s.slab->I16.cap);
  size_t want[MB + 1]; size_t k;
  r_result w = ref_v1(U(s.t), s.n, U(s.p), s.m, s.cs, want, &k);
  fzf_result_t r = fzf_fuzzy_match_v2(s.cs, s.norm, &s.text, &s.pat, s.pr.p, s.slab);
  check_res(r, w); check_pos(&s.pr, want, k);
}

// The full result and positions equal fzf 0.27.0's FuzzyMatchV2 (spec.h
// ref_v2), with a zeroed slab (= a fresh slab, = no slab) and positions
// requested. With a used slab this holds for the score and end only
// (h_v2_slab_independent), unless the stale-slab fix is applied.
void h_v2_full(void) {
  setup s; any_setup(&s);
  s.slab = big_slab(true);
  fzf_position_t q = {malloc((MB + 1) * sizeof(uint32_t)), 0, MB + 1};
  size_t want[MB + 1]; size_t k;
  r_result w = ref_v2(U(s.t), s.n, U(s.p), s.m, s.cs, want, &k);
  fzf_result_t r = fzf_fuzzy_match_v2(s.cs, s.norm, &s.text, &s.pat, &q, s.slab);
  check_res(r, w);
  __CPROVER_assert(q.size == k, "positions: count");
  for (size_t i = 0; i < k && i < q.size; i++) __CPROVER_assert(q.data[i] == want[i], "positions = fzf's");
}

// The slab's stale contents never change v2's result or positions: a call
// with a slab holding arbitrary data equals a call with a zeroed slab (which
// is what a fresh slab, or no slab, gives). Fails on the fixed copy for start
// and positions (findings/v2-stale-slab-and-other-findings.md, 1).
void h_v2_slab_independent(void) {
  setup s; any_setup(&s);
  fzf_slab_t *dirty = big_slab(false), *clean = big_slab(true);
  fzf_position_t q1 = {malloc(MB * sizeof(uint32_t)), 0, MB}, q2 = {malloc(MB * sizeof(uint32_t)), 0, MB};
  fzf_position_t *p1 = &q1, *p2 = &q2;
  fzf_result_t a = fzf_fuzzy_match_v2(s.cs, s.norm, &s.text, &s.pat, p1, dirty);
  fzf_result_t b = fzf_fuzzy_match_v2(s.cs, s.norm, &s.text, &s.pat, p2, clean);
  __CPROVER_assert(a.score == b.score && a.end == b.end, "same score and end");
  __CPROVER_assert(a.start == b.start, "same start");
  __CPROVER_assert(p1->size == p2->size, "same number of positions");
  for (size_t i = 0; i < p1->size && i < p2->size; i++) __CPROVER_assert(p1->data[i] == p2->data[i], "same positions");
}
