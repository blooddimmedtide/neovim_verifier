// CBMC: fzf_get_score / fzf_get_positions / fzf_free_positions as a
// composition. The term algorithms are replaced by a stub that has the
// properties proved for the real algorithms in harness_match.c:
//  - no match: start = end = -1, score 0, nothing appended;
//  - match: 0 <= start <= end <= text size, any score, and, when pos is not
//    NULL, a few positions appended, each inside the text.
// The pattern object is built directly: any number of AND-sets <= SETS, each
// with 1..TERMS terms, each term inverse or not. only_inv follows the parser's
// rule (every set one inverse term), which h_parse checks against ref_parse.
// The stub returns the same result for the same term on every call, as the real
// algorithms do for the same text and pattern.
// With -DINTENDED it also asserts fzf's rule that every line whose sets all
// match is kept (score != 0 for the Telescope sorter). CBMC refutes this:
// findings/v2-stale-slab-and-other-findings.md, items 2 and 3.
#include <stdlib.h>
#include <string.h>
#include "harness_util.h"
#include FZF_C

#ifndef SETS
#define SETS 2
#endif
#ifndef TERMS
#define TERMS 2
#endif
#ifndef TL
#define TL 3
#endif
#define NT (SETS * TERMS)
#define MAXP 2   // positions a stub appends on a match

size_t nondet_size(void);
bool nondet_bool(void);
int32_t nondet_i32(void);

static fzf_string_t texts[NT];
static fzf_result_t res[NT];
static size_t npos[NT];        // positions the stub appends on a match
static uint32_t posv[NT][MAXP];
static size_t calls_with_pos[NT];

static size_t term_index(fzf_string_t *p) {
  for (size_t k = 0; k < NT; k++)
    if (p == &texts[k]) return k;
  __CPROVER_assert(0, "algorithm called with a term of the pattern");
  return 0;
}

static fzf_result_t stub_alg(bool cs, bool norm, fzf_string_t *input, fzf_string_t *pattern,
                             fzf_position_t *pos, fzf_slab_t *slab) {
  (void)cs; (void)norm; (void)slab;
  size_t k = term_index(pattern);
  if (res[k].start >= 0 && pos) {
    calls_with_pos[k]++;
    for (size_t i = 0; i < npos[k]; i++) append_pos(pos, posv[k][i]);
  }
  return res[k];
}

void h_compose(void) {
  size_t tn = nondet_size();
  __CPROVER_assume(tn <= TL);
  char *t = exact_malloc(tn + 1, TL + 1, 1);
  for (size_t i = 0; i < tn; i++) __CPROVER_assume(t[i] != 0);
  t[tn] = 0;

  for (size_t k = 0; k < NT; k++) {
    bool m = nondet_bool();
    if (m) {
      res[k].start = nondet_i32(); res[k].end = nondet_i32(); res[k].score = nondet_i32();
      __CPROVER_assume(res[k].start >= 0 && res[k].start <= res[k].end && (size_t)res[k].end <= tn);
      __CPROVER_assume(res[k].score > -(1 << 28) && res[k].score < (1 << 28));
      npos[k] = nondet_size();
      __CPROVER_assume(npos[k] <= MAXP);
      for (size_t i = 0; i < MAXP; i++) {
        posv[k][i] = (uint32_t)nondet_size();
        __CPROVER_assume(posv[k][i] < tn);
      }
    } else {
      res[k] = (fzf_result_t){-1, -1, 0};
      npos[k] = 0;
    }
    calls_with_pos[k] = 0;
  }

  // the pattern object
  size_t ns = nondet_size();
  __CPROVER_assume(ns <= SETS);
  fzf_pattern_t po = {NULL, 0, 0, false};
  fzf_term_set_t sets[SETS];
  fzf_term_set_t *setp[SETS];
  fzf_term_t terms[SETS][TERMS];
  bool only = true;
  for (size_t i = 0; i < ns; i++) {
    size_t n = nondet_size();
    __CPROVER_assume(n >= 1 && n <= TERMS);
    for (size_t j = 0; j < n; j++) {
      terms[i][j] = (fzf_term_t){stub_alg, nondet_bool(), NULL, &texts[i * TERMS + j], nondet_bool()};
    }
    sets[i] = (fzf_term_set_t){terms[i], n, n};
    setp[i] = &sets[i];
    if (n > 1 || !terms[i][0].inv) only = false;
  }
  if (ns > 0) { po.ptr = setp; po.size = ns; po.cap = ns; po.only_inv = only; }

  fzf_slab_t *slab = NULL;   // the stub ignores it; slab use is proved per algorithm
  int32_t sc = fzf_get_score(t, &po, slab);
  fzf_position_t *pos = fzf_get_positions(t, &po, slab);

  if (ns == 0) {
    __CPROVER_assert(sc == 1 && pos == NULL, "empty pattern: score 1, no positions");
  } else {
    bool all = true; int64_t total = 0; bool any_inv_match = false; int64_t inv_sum = 0;
    size_t want_pos = 0;
    for (size_t i = 0; i < ns; i++) {
      bool ok = false; int32_t cur = 0;
      for (size_t j = 0; j < sets[i].size; j++) {
        size_t k = i * TERMS + j;
        bool m = res[k].start >= 0;
        if (terms[i][j].inv) {
          if (m) any_inv_match = true; else ok = true;
        } else if (m) { cur = res[k].score; ok = true; want_pos += npos[k]; break; }
      }
      if (!ok) all = false;
      total += ok ? cur : 0;
      if (po.only_inv) inv_sum += res[i * TERMS].score;
    }
    if (po.only_inv) {
      __CPROVER_assert(sc == (inv_sum > 0 ? 0 : 1), "only inverse terms: 1 iff the scores sum to <= 0");
      __CPROVER_assert(!(all && any_inv_match), "only inverse terms: all sets match iff no term matches");
    } else {
      __CPROVER_assert(sc == (all ? total : 0), "score: sum of the sets' scores, 0 when a set fails");
    }
    __CPROVER_assert((pos != NULL) == all, "positions returned iff every set matches");
    if (pos) {
      __CPROVER_assert(pos->size == want_pos, "positions: those of the first matching non-inverse term of each set");
      __CPROVER_assert(pos->size <= pos->cap, "size <= cap");
      for (size_t k = 0; k < pos->size; k++) __CPROVER_assert(pos->data[k] < tn, "every position inside the text");
    }
#ifdef INTENDED
    __CPROVER_assert(!all || sc != 0, "fzf: a line whose sets all match is kept (score != 0)");
#endif
  }
  for (size_t k = 0; k < NT; k++)
    __CPROVER_assert(calls_with_pos[k] <= 1, "positions requested at most once per term");
  fzf_free_positions(pos);
  free(t);
}

// fzf_make_slab / fzf_free_slab: buffers of the requested sizes, zeroed,
// size 0, everything freed.
void h_slab(void) {
  size_t a = nondet_size(), b = nondet_size();
  __CPROVER_assume(a <= 6 && b <= 6);
  fzf_slab_t *s = fzf_make_slab((fzf_slab_config_t){a, b});
  __CPROVER_assert(s->I16.cap == a && s->I16.size == 0 && s->I32.cap == b && s->I32.size == 0, "capacities");
  for (size_t i = 0; i < a; i++) __CPROVER_assert(s->I16.data[i] == 0, "I16 zeroed");
  for (size_t i = 0; i < b; i++) __CPROVER_assert(s->I32.data[i] == 0, "I32 zeroed");
  if (a) s->I16.data[a - 1] = 1;   // writable to the end
  if (b) s->I32.data[b - 1] = 1;
  fzf_free_slab(s);
}
