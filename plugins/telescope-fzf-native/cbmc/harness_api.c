// CBMC: the public interface of fzf.c: fzf_parse_pattern / fzf_free_pattern,
// fzf_get_score, fzf_get_positions / fzf_free_positions, fzf_make_slab /
// fzf_free_slab. Run with --memory-leak-check: everything allocated is freed
// by the matching free function.
#include <stdlib.h>
#include <string.h>
#include "spec.h"
#include "harness_util.h"
#ifdef FZFV_CODE_MALLOC
#define malloc fzfv_code_malloc   // see harness_util.h
#endif
#include FZF_C
#undef malloc

#ifndef PL
#define PL 4   // pattern length bound for h_parse
#endif
#ifndef QL
#define QL 3   // pattern length bound for the score / positions harnesses
#endif
#ifndef TL
#define TL 3   // text length bound
#endif
#define MAXT (PL / 2 + 1)   // at most this many tokens in a pattern of length PL

size_t nondet_size(void);
bool nondet_bool(void);
int nondet_int(void);

static char *any_str(size_t max, size_t *len) {
  size_t n = nondet_size();
  __CPROVER_assume(n <= max);
  char *s = exact_malloc(n + 1, max + 1, 1);
  for (size_t i = 0; i < n; i++) __CPROVER_assume(s[i] != 0);
  s[n] = 0;
  *len = n;
  return s;
}

#include "spec_parse.h"

static fzf_algo_t algo_of(int fn) {
  return fn == A_V2 ? fzf_fuzzy_match_v2 : fn == A_EXACT ? fzf_exact_match_naive
       : fn == A_PREFIX ? fzf_prefix_match : fn == A_SUFFIX ? fzf_suffix_match : fzf_equal_match;
}
static void check_parse(fzf_pattern_t *po, rpat *rp) {
  __CPROVER_assert(po != NULL, "pattern object");
  __CPROVER_assert(po->size == rp->n, "number of AND-sets");
  __CPROVER_assert((po->ptr == NULL) == (rp->n == 0), "ptr NULL iff no terms (get_score's 'match all')");
  __CPROVER_assert(rp->n == 0 || po->only_inv == rp->only_inv, "only_inv");
  for (size_t i = 0; i < po->size && i < rp->n; i++) {
    fzf_term_set_t *s = po->ptr[i];
    __CPROVER_assert(s->size == rp->s[i].n && s->size <= s->cap, "set size");
    for (size_t j = 0; j < s->size && j < rp->s[i].n; j++) {
      fzf_term_t *t = &s->ptr[j];
      rterm *r = &rp->s[i].t[j];
      fzf_string_t *x = (fzf_string_t *)t->text;
      __CPROVER_assert(t->fn == algo_of(r->fn) && t->inv == r->inv && t->case_sensitive == r->cs, "term kind");
      __CPROVER_assert(x->size == r->len, "term length");
      for (size_t k = 0; k <= r->len; k++) __CPROVER_assert(x->data[k] == r->text[k], "term text (NUL-terminated)");
    }
  }
}

// Every pattern string of length 0..PL, every byte, every case mode, fuzzy
// or not: parse gives the reference's terms; free releases everything.
void h_parse(void) {
  size_t n;
  char *in = any_str(PL, &n);
  char copy[PL + 1];
  for (size_t i = 0; i <= n; i++) copy[i] = in[i];
  int mode = nondet_int();
  __CPROVER_assume(mode >= CaseSmart && mode <= CaseRespect);
  bool fuzzy = nondet_bool();
  rpat rp;
  ref_parse(copy, n, mode, fuzzy, &rp);
  fzf_pattern_t *po = fzf_parse_pattern((fzf_case_types)mode, false, in, fuzzy);
  check_parse(po, &rp);
  fzf_free_pattern(po);
  free(in);   // the caller's buffer (parse writes NULs over trailing spaces in it)
}

// Same check, longer patterns, but every byte from the alphabet the parser
// treats specially plus one lower- and one upper-case letter (h_parse covers
// every byte value for shorter patterns).
void h_parse_alpha(void) {
  size_t n = nondet_size();
  __CPROVER_assume(n <= PL);
  char *in = exact_malloc(n + 1, PL + 1, 1);
  static const char alpha[] = {' ', '\\', '!', '^', '$', '\'', '|', '\t', 'a', 'A'};
  for (size_t i = 0; i < n; i++) {
    unsigned k = (unsigned)nondet_int();
    __CPROVER_assume(k < sizeof alpha);
    in[i] = alpha[k];
  }
  in[n] = 0;
  char copy[PL + 1];
  for (size_t i = 0; i <= n; i++) copy[i] = in[i];
  int mode = nondet_int();
  __CPROVER_assume(mode >= CaseSmart && mode <= CaseRespect);
  bool fuzzy = nondet_bool();
  rpat rp;
  ref_parse(copy, n, mode, fuzzy, &rp);
  fzf_pattern_t *po = fzf_parse_pattern((fzf_case_types)mode, false, in, fuzzy);
  check_parse(po, &rp);
  fzf_free_pattern(po);
  free(in);
}

static bool term_matches(fzf_term_t *t, fzf_string_t *in, fzf_slab_t *slab, int32_t *score) {
  fzf_result_t r = CALL_ALG(t, false, (*in), NULL, slab);
  *score = r.score;
  return r.start >= 0;
}

// get_score / get_positions combine the terms as fzf's extended search says:
// a pattern matches when every AND-set has a term that matches (or an
// inverse term that does not); the score is the sum over sets of the first
// matching non-inverse term's score; an only-inverse pattern scores 1 when
// it matches and 0 otherwise. The term results come from calling the term's
// algorithm (proved separately in harness_match.c) on the same input.
void h_score_positions(void) {
  size_t qn, tn;
  char *q = any_str(QL, &qn), *t = any_str(TL, &tn);
  int mode = nondet_int();
  __CPROVER_assume(mode >= CaseSmart && mode <= CaseRespect);
  fzf_pattern_t *po = fzf_parse_pattern((fzf_case_types)mode, false, q, nondet_bool());
  // no slab, a slab too small for v2 (falls back to v1 / mallocs), or one
  // big enough for every buffer v2 takes from it
  fzf_slab_t *slab = NULL;
  int which = nondet_int();
  if (which == 1) slab = fzf_make_slab((fzf_slab_config_t){4, 2});
  if (which == 2) slab = fzf_make_slab((fzf_slab_config_t){3 * TL + 2 * TL * QL + 1, 2 * TL + 1});

  int32_t sc = fzf_get_score(t, po, slab);
  fzf_position_t *pos = fzf_get_positions(t, po, slab);

  fzf_string_t in = {t, tn};
  if (po->ptr == NULL) {
    __CPROVER_assert(sc == 1 && pos == NULL, "empty pattern: score 1, no positions");
  } else {
    bool all = true; int32_t total = 0; bool any_inv_match = false;
    for (size_t i = 0; i < po->size; i++) {
      fzf_term_set_t *s = po->ptr[i];
      bool ok = false; int32_t cur = 0;
      for (size_t j = 0; j < s->size; j++) {
        int32_t v;
        bool m = term_matches(&s->ptr[j], &in, slab, &v);
        if (s->ptr[j].inv) {
          if (m) { any_inv_match = true; __CPROVER_assert(v > 0, "a match of an inverse (exact) term scores > 0"); }
          else ok = true;
        } else if (m) { cur = v; ok = true; break; }
      }
      if (!ok) all = false;
      total += ok ? cur : 0;
    }
    if (po->only_inv) __CPROVER_assert(sc == (any_inv_match ? 0 : 1), "only inverse terms: 1 iff none matches");
    else __CPROVER_assert(sc == (all ? total : 0), "score: sum of the sets' scores, 0 when a set fails");
    __CPROVER_assert((pos != NULL) == all, "positions returned iff every set matches");
    if (pos) {
      __CPROVER_assert(pos->size <= pos->cap, "size <= cap");
      for (size_t k = 0; k < pos->size; k++) __CPROVER_assert(pos->data[k] < tn, "every position inside the text");
    }
  }
  fzf_free_positions(pos);
  fzf_free_pattern(po);
  fzf_free_slab(slab);
  free(q);
  free(t);
}
