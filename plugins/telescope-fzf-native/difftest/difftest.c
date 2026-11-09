// Differential test: fzf.c (compiled with gcc -O2 and ASan/UBSan, real glibc,
// "C" locale) against the reference specification in ../cbmc/spec.h and
// ../cbmc/spec_parse.h, on random inputs far longer than the CBMC bounds.
// Usage: dt <iterations> <seed>. Exit 1 on the first mismatch (printed).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define PL 40
#define MAXT (PL / 2 + 1)
#include "spec.h"
#include FZF_C
#include "spec_parse.h"

static uint64_t rs;
static uint64_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }
static size_t rn(size_t n) { return n ? rnd() % n : 0; }
static const char ALPHA[] = "aaabbcAABBC01 _/-.\t";
static char rbyte(void) {
  int k = rn(20);
  if (k < 17) return ALPHA[rn(sizeof ALPHA - 1)];
  if (k < 19) return (char)(0x80 + rn(128));
  return (char)(1 + rn(255));
}
static long fails = 0;
#define CHECK(c, ...) do { if (!(c)) { fprintf(stderr, __VA_ARGS__); fputc('\n', stderr); fails++; dump(); exit(1); } } while (0)
static char T[64], P[64]; static size_t N, M; static bool CS; static const char *ALG;
static void dump(void) {
  fprintf(stderr, "alg=%s cs=%d text(%zu)=", ALG, CS, N);
  for (size_t i = 0; i < N; i++) fprintf(stderr, "%02x", (unsigned char)T[i]);
  fprintf(stderr, " pat(%zu)=", M);
  for (size_t i = 0; i < M; i++) fprintf(stderr, "%02x", (unsigned char)P[i]);
  fputc('\n', stderr);
}
static fzf_slab_t *dirty_slab(size_t c16, size_t c32) {
  fzf_slab_t *s = fzf_make_slab((fzf_slab_config_t){c16, c32});
  for (size_t i = 0; i < c16; i++) s->I16.data[i] = (int16_t)rnd();
  for (size_t i = 0; i < c32; i++) s->I32.data[i] = (int32_t)rnd();
  return s;
}
static fzf_slab_t *any_slab(void) {
  switch (rn(4)) {
    case 0: return NULL;
    case 1: return fzf_make_default_slab();
    case 2: return dirty_slab(rn(200), rn(40));
    default: return dirty_slab(4096, 256);
  }
}
static fzf_position_t *any_pos(size_t *os) {
  if (rn(4) == 0) { *os = 0; return NULL; }
  fzf_position_t *p = fzf_pos_array(rn(4));
  size_t pre = rn(3);
  for (size_t i = 0; i < pre; i++) append_pos(p, 1000 + i);
  *os = p->size;
  return p;
}
static void check_pos(fzf_position_t *p, size_t os, const size_t *want, size_t k) {
  if (!p) return;
  CHECK(p->size == os + k, "positions: count %zu want %zu", p->size - os, k);
  for (size_t i = 0; i < os; i++) CHECK(p->data[i] == 1000 + i, "positions: old");
  for (size_t i = 0; i < k; i++) CHECK(p->data[os + i] == want[i], "positions[%zu]=%u want %zu", i, p->data[os + i], want[i]);
}
typedef r_result (*reff)(const unsigned char *, size_t, const unsigned char *, size_t, bool, size_t *, size_t *);

static void gen_case(void) {
  N = rn(25);
  for (size_t i = 0; i < N; i++) T[i] = rbyte();
  M = rn(7);
  if (N && rn(2)) {   // a subsequence of the text, often lowercased: likely to match
    size_t k = 0;
    for (size_t i = 0; i < N && k < M; i++) if (rn(3) == 0) P[k++] = T[i];
    M = k;
    if (rn(2)) for (size_t i = 0; i < M; i++) P[i] = (char)r_fold((unsigned char)P[i], false);
  } else if (N && rn(2)) {   // a substring
    size_t a = rn(N); if (a + M > N) M = N - a;
    memcpy(P, T + a, M);
    if (rn(2)) for (size_t i = 0; i < M; i++) P[i] = (char)r_fold((unsigned char)P[i], false);
  } else for (size_t i = 0; i < M; i++) P[i] = rbyte();
  CS = rn(2);
}
static void one_alg(const char *name, fzf_algo_t fn, reff ref) {
  ALG = name;
  char *t = malloc(N ? N : 1), *p = malloc(M ? M : 1);   // exact-size heap objects for ASan
  memcpy(t, T, N); memcpy(p, P, M);
  fzf_string_t text = {t, N}, pat = {p, M};
  size_t os; fzf_position_t *pos = any_pos(&os);
  fzf_slab_t *slab = any_slab();
  size_t want[64], k;
  r_result w = ref((const unsigned char *)T, N, (const unsigned char *)P, M, CS, want, &k);
  fzf_result_t r = fn(CS, rn(2), &text, &pat, pos, slab);
  CHECK(r.start == w.start && r.end == w.end && r.score == w.score,
        "%s: got (%d,%d,%d) want (%d,%d,%d)", name, r.start, r.end, r.score, w.start, w.end, w.score);
  check_pos(pos, os, want, k);
  fzf_free_positions(pos); fzf_free_slab(slab); free(t); free(p);
}
static long slab_dep = 0, slab_dep_score = 0, v2_ref_checked = 0;
static long v2_m1 = 0, v2_multi = 0, v2_fallback = 0;
static void one_v2(void) {
  ALG = "v2";
  char *t = malloc(N ? N : 1), *p = malloc(M ? M : 1);
  memcpy(t, T, N); memcpy(p, P, M);
  fzf_string_t text = {t, N}, pat = {p, M};
  size_t os; fzf_position_t *pos = any_pos(&os);
  fzf_slab_t *slab = any_slab();
  size_t want[64], k;
  fzf_result_t r = fzf_fuzzy_match_v2(CS, rn(2), &text, &pat, pos, slab);
  const unsigned char *ut = (const unsigned char *)T, *up = (const unsigned char *)P;
  if (M == 0) { CHECK(r.start == 0 && r.end == 0 && r.score == 0, "v2 empty"); check_pos(pos, os, want, 0); goto out; }
  if (slab && N * M > slab->I16.cap) {
    v2_fallback++;
    r_result w = ref_v1(ut, N, up, M, CS, want, &k);
    CHECK(r.start == w.start && r.end == w.end && r.score == w.score, "v2 fallback = v1");
    check_pos(pos, os, want, k);
    goto out;
  }
  if (!r_subseq(ut, 0, N, up, M, CS)) { CHECK(r.start == -1 && r.end == -1 && r.score == 0, "v2 no match"); check_pos(pos, os, want, 0); goto out; }
  CHECK(0 <= r.start && r.start < r.end && (size_t)r.end <= N && r.score >= R_MATCH, "v2 range (%d,%d,%d)", r.start, r.end, r.score);
  if (M == 1) {
    v2_m1++;
    size_t best = N; int bb = -1;
    for (size_t i = 0; i < N; i++) if (r_fold(ut[i], CS) == up[0] && r_bonus_at(ut, i) > bb) { best = i; bb = r_bonus_at(ut, i); }
    CHECK(r.start == (int32_t)best && r.end == (int32_t)best + 1 && r.score == R_MATCH + 2 * bb, "v2 M=1");
    want[0] = best; check_pos(pos, os, want, 1);
    goto out;
  }
  v2_multi++;
  if (pos) {
    CHECK(pos->size == os + M, "v2 count");
    for (size_t q = 0; q < M; q++) {
      uint32_t x = pos->data[os + q];
      CHECK(x < N && r_fold(ut[x], CS) == up[M - 1 - q], "v2 position %zu", q);
      if (q) CHECK(x < pos->data[os + q - 1], "v2 decreasing");
    }
    CHECK((uint32_t)r.start == pos->data[os + M - 1] && (uint32_t)r.end == pos->data[os] + 1, "v2 start/end = positions");
  }
  {
    // full result against fzf 0.27.0's FuzzyMatchV2 (spec.h ref_v2), with no
    // slab (zeroed matrices) and positions requested
    fzf_position_t *p3 = fzf_pos_array(0);
    fzf_result_t b = fzf_fuzzy_match_v2(CS, false, &text, &pat, p3, NULL);
    r_result w = ref_v2(ut, N, up, M, CS, want, &k);
    CHECK(b.start == w.start && b.end == w.end && b.score == w.score,
          "v2 vs fzf: got (%d,%d,%d) want (%d,%d,%d)", b.start, b.end, b.score, w.start, w.end, w.score);
    CHECK(p3->size == k, "v2 vs fzf: count");
    for (size_t i = 0; i < k; i++) CHECK(p3->data[i] == want[i], "v2 vs fzf: position %zu", i);
    v2_ref_checked++;
    // slab independence: the same call with the (used) slab
    if (slab) {
      fzf_position_t *p2 = fzf_pos_array(0);
      fzf_result_t a = fzf_fuzzy_match_v2(CS, false, &text, &pat, p2, slab);
      // findings/v2-stale-slab-and-other-findings.md 1: counted, not fatal, so
      // the other checks keep running on files that still have that defect.
      bool same = a.start == b.start && a.end == b.end && a.score == b.score && p2->size == p3->size;
      for (size_t i = 0; same && i < p2->size; i++) same = p2->data[i] == p3->data[i];
      if (!same) { slab_dep++; if (a.score != b.score) slab_dep_score++; }
      fzf_free_positions(p2);
    }
    fzf_free_positions(p3);
  }
out:
  fzf_free_positions(pos); fzf_free_slab(slab); free(t); free(p);
}

static const char PALPHA[] = "aAb ^$!'|\\\t.";
static fzf_algo_t algo_of(int fn) {
  return fn == A_V2 ? fzf_fuzzy_match_v2 : fn == A_EXACT ? fzf_exact_match_naive
       : fn == A_PREFIX ? fzf_prefix_match : fn == A_SUFFIX ? fzf_suffix_match : fzf_equal_match;
}
static void one_parse_and_score(void) {
  ALG = "parse/score";
  size_t n = rn(16);
  char in[PL + 1], copy[PL + 1];
  for (size_t i = 0; i < n; i++) in[i] = rn(8) ? PALPHA[rn(sizeof PALPHA - 1)] : rbyte();
  for (size_t i = 0; i < n; i++) if (!in[i]) in[i] = 'a';
  in[n] = 0; memcpy(copy, in, n + 1);
  memcpy(P, in, n); M = n;
  int mode = rn(3); bool fuzzy = rn(2);
  rpat rp; ref_parse(copy, n, mode, fuzzy, &rp);
  char *heap = malloc(n + 1); memcpy(heap, in, n + 1);
  fzf_pattern_t *po = fzf_parse_pattern((fzf_case_types)mode, false, heap, fuzzy);
  CHECK(po->size == rp.n && (po->ptr == NULL) == (rp.n == 0), "parse: sets %zu want %zu", po->size, rp.n);
  if (rp.n) CHECK(po->only_inv == rp.only_inv, "parse: only_inv");
  for (size_t i = 0; i < rp.n; i++) {
    CHECK(po->ptr[i]->size == rp.s[i].n, "parse: set size");
    for (size_t j = 0; j < rp.s[i].n; j++) {
      fzf_term_t *t = &po->ptr[i]->ptr[j]; rterm *r = &rp.s[i].t[j];
      fzf_string_t *x = t->text;
      CHECK(t->fn == algo_of(r->fn) && t->inv == r->inv && t->case_sensitive == r->cs, "parse: term kind");
      CHECK(x->size == r->len && memcmp(x->data, r->text, r->len + 1) == 0, "parse: term text");
    }
  }
  // score / positions on a random text
  gen_case();
  char *t = malloc(N + 1);
  for (size_t i = 0; i < N; i++) t[i] = T[i] ? T[i] : 'a';
  t[N] = 0;
  fzf_slab_t *slab = any_slab();
  int32_t sc = fzf_get_score(t, po, slab);
  fzf_position_t *pos = fzf_get_positions(t, po, slab);
  fzf_string_t in2 = {t, N};
  if (!po->ptr) CHECK(sc == 1 && !pos, "empty pattern");
  else {
    bool all = true, any_inv = false; int32_t total = 0;
    for (size_t i = 0; i < po->size; i++) {
      fzf_term_set_t *s = po->ptr[i]; bool ok = false; int32_t cur = 0;
      for (size_t j = 0; j < s->size; j++) {
        fzf_result_t r = CALL_ALG((&s->ptr[j]), false, in2, NULL, slab);   // same slab: v2 falls back to v1 when it is small
        bool m = r.start >= 0;
        if (s->ptr[j].inv) { if (m) { any_inv = true; CHECK(r.score > 0, "inverse match scores > 0"); } else ok = true; }
        else if (m) { cur = r.score; ok = true; break; }
      }
      if (!ok) all = false;
      total += ok ? cur : 0;
    }
    if (po->only_inv) CHECK(sc == (any_inv ? 0 : 1), "only_inv score %d", sc);
    else CHECK(sc == (all ? total : 0), "get_score %d want %d", sc, all ? total : 0);
    CHECK((pos != NULL) == all, "positions iff match");
    if (pos) for (size_t k = 0; k < pos->size; k++) CHECK(pos->data[k] < N, "position in text");
  }
  fzf_free_positions(pos); fzf_free_pattern(po); fzf_free_slab(slab); free(heap); free(t);
}

int main(int argc, char **argv) {
  long iters = argc > 1 ? atol(argv[1]) : 100000;
  rs = argc > 2 ? strtoull(argv[2], 0, 0) : 88172645463325252ull;
  if (!rs) rs = 1;
  for (long it = 0; it < iters; it++) {
    gen_case();
    one_alg("prefix", fzf_prefix_match, ref_prefix);
    one_alg("suffix", fzf_suffix_match, ref_suffix);
    one_alg("equal", fzf_equal_match, ref_equal);
    one_alg("exact", fzf_exact_match_naive, ref_exact);
    one_alg("v1", fzf_fuzzy_match_v1, ref_v1);
    one_v2();
    one_parse_and_score();
  }
  printf("%ld iterations x 7 checks, 0 mismatches (v2: %ld one-byte, %ld multi-byte, %ld fallback; %ld compared with fzf's v2 in full)\n",
         iters, v2_m1, v2_multi, v2_fallback, v2_ref_checked);
  printf("v2 with a used slab differs from v2 with a fresh one: %ld cases (%ld with a different score)\n",
         slab_dep, slab_dep_score);
  return slab_dep ? 2 : 0;
}
