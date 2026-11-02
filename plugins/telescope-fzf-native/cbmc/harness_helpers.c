// CBMC: functional correctness of fzf.c's small helpers against spec.h.
// Finite-domain helpers are proved for every input. Helpers that loop over a
// buffer get exact-size objects of every length 0..NB (pointer check: no read
// outside the object); their unbounded proofs are in ../wp/ where available.
#include <stdlib.h>
#include <string.h>
#include "spec.h"
#include "harness_util.h"
#include FZF_C   // the file under test, unchanged (run_cbmc.sh checks its sha256)

#ifndef NB
#define NB 6
#endif

size_t nondet_size(void);
int nondet_int(void);
char nondet_char(void);
bool nondet_bool(void);
int16_t nondet_i16(void);
int32_t nondet_i32(void);

// n arbitrary bytes in an object of exactly n bytes (NULL-free, n may be 0).
static char *any_buf(size_t n) {
  return exact_malloc(n, NB, 1);
}
// A NUL-terminated string of length n <= max in an object of exactly n+1 bytes.
static char *any_str(size_t max, size_t *len) {
  size_t n = nondet_size();
  __CPROVER_assume(n <= max);
  char *s = exact_malloc(n + 1, max + 1, 1);
  for (size_t i = 0; i < n; i++) __CPROVER_assume(s[i] != 0);
  s[n] = 0;
  *len = n;
  return s;
}
static size_t any_len(void) { size_t n = nondet_size(); __CPROVER_assume(n <= NB); return n; }
#define U(p) ((const unsigned char *)(p))

// ---- finite domains: every input ----
void h_char_class(void) {
  char ch = nondet_char();
  int r = r_class((unsigned char)ch);
  __CPROVER_assert(char_class_of_ascii(ch) == r, "char_class_of_ascii = class");
  __CPROVER_assert(char_class_of(ch) == r, "char_class_of = class");
}
void h_bonus_for(void) {
  int32_t p = nondet_i32(), c = nondet_i32();
  // the domain: the classes char_class_of returns, plus CharLetter (3), unused
  __CPROVER_assume(0 <= p && p <= 4 && 0 <= c && c <= 4);
  __CPROVER_assert(bonus_for(p, c) == r_bonus(p, c), "bonus_for = fzf bonusFor");
}
void h_small(void) {
  char r = nondet_char();
  __CPROVER_assert(normalize_rune(r) == r, "normalize_rune is the identity");
  size_t n = nondet_size();
  __CPROVER_assert(is_ascii(NULL, n) == true, "is_ascii is always true (body commented out)");
  int16_t a = nondet_i16(), b = nondet_i16();
  __CPROVER_assert(max16(a, b) == (a > b ? a : b) && (max16(a, b) == a || max16(a, b) == b), "max16");
  size_t x = nondet_size(), y = nondet_size();
  __CPROVER_assert(min64u(x, y) <= x && min64u(x, y) <= y && (min64u(x, y) == x || min64u(x, y) == y), "min64u");
}

// ---- loops over a buffer: every length 0..NB, every content ----
void h_index_byte(void) {
  size_t n = any_len();
  char *d = any_buf(n);
  char b = nondet_char();
  fzf_string_t s = {d, n};
  int32_t r = index_byte(&s, b);
  if (r < 0) {
    __CPROVER_assert(r == -1, "-1 when absent");
    for (size_t i = 0; i < n; i++) __CPROVER_assert(d[i] != b, "absent");
  } else {
    __CPROVER_assert((size_t)r < n && d[r] == b, "found");
    for (size_t i = 0; i < (size_t)r; i++) __CPROVER_assert(d[i] != b, "first");
  }
}
void h_bonus_at(void) {
  size_t n = any_len();
  char *d = any_buf(n);
  size_t i = nondet_size();
  __CPROVER_assume(i < n);
  fzf_string_t s = {d, n};
  __CPROVER_assert(bonus_at(&s, i) == r_bonus_at(U(d), i), "bonus_at");
}
void h_whitespaces(void) {
  size_t n = any_len();
  char *d = any_buf(n);
  fzf_string_t s = {d, n};
  size_t l = leading_whitespaces(&s), t = trailing_whitespaces(&s);
  __CPROVER_assert(l <= n && t <= n, "counts within the text");
  for (size_t i = 0; i < l; i++) __CPROVER_assert(r_space(U(d)[i]), "leading are white");
  __CPROVER_assert(l == n || !r_space(U(d)[l]), "leading maximal");
  for (size_t i = n - t; i < n; i++) __CPROVER_assert(r_space(U(d)[i]), "trailing are white");
  __CPROVER_assert(t == n || !r_space(U(d)[n - t - 1]), "trailing maximal");
}
void h_copy(void) {
  size_t n = any_len();
  char *d = any_buf(n);
  fzf_string_t s = {d, n};
  int32_t *o = exact_malloc(n, NB, sizeof(int32_t));
  fzf_i32_t dst = {o, n, n, false};
  copy_runes(&s, &dst);
  for (size_t i = 0; i < n; i++) __CPROVER_assert(o[i] == (int32_t)d[i], "copy_runes: sign-extended char");
  int16_t *a = exact_malloc(n, NB, sizeof(int16_t)), *b = exact_malloc(n, NB, sizeof(int16_t));
  i16_slice_t src = {a, n};
  fzf_i16_t d16 = {b, n, n, false};
  copy_into_i16(&src, &d16);
  for (size_t i = 0; i < n; i++) __CPROVER_assert(b[i] == a[i], "copy_into_i16");
}
static bool ref_strneq(const char *a, const char *b, size_t n) {   // C11 strncmp(a, b, n) == 0
  for (size_t i = 0; i < n; i++) {
    if (a[i] != b[i]) return false;
    if (a[i] == 0) return true;
  }
  return true;
}
void h_prefix_suffix(void) {
  size_t n, k;
  char *s = any_str(NB, &n), *p = any_str(3, &k);
  size_t pl = nondet_size();
  __CPROVER_assume(pl <= k + 1);   // callers pass the literal's length; any length up to its NUL
  __CPROVER_assert(has_prefix(s, p, pl) == ref_strneq(p, s, pl), "has_prefix");
  size_t len = nondet_size();
  __CPROVER_assume(len <= n);      // callers: len is the string's length (or a prefix of it)
  bool want = len >= pl && ref_strneq(s + (len - pl), p, pl);
  __CPROVER_assert(has_suffix(s, len, p, pl) == (len >= pl && want), "has_suffix");
}
void h_str_tolower(void) {
  size_t n = any_len();
  char *d = any_buf(n);
  char before[NB];
  for (size_t i = 0; i < n; i++) before[i] = d[i];
  char *r = str_tolower(d, n);
  __CPROVER_assert(__CPROVER_OBJECT_SIZE(r) == n + 1 && __CPROVER_POINTER_OFFSET(r) == 0, "fresh object of n+1 bytes");
  for (size_t i = 0; i < n; i++) {
    __CPROVER_assert(U(r)[i] == r_fold(U(before)[i], false), "folded");
    __CPROVER_assert(d[i] == before[i], "input unchanged");
  }
  __CPROVER_assert(r[n] == 0, "NUL");
  free(r);
}
void h_trim_left(void) {
  size_t n;
  char *s = any_str(NB, &n);
  size_t len = nondet_size();
  __CPROVER_assume(len <= n);
  size_t l0 = len;
  char *r = trim_whitespace_left(s, &len);
  size_t k = 0;
  while (k < l0 && s[k] == ' ') k++;
  // DEFECT (findings/trim-whitespace-left.md): the loop counts i up while *len
  // goes down, so at most ceil(len/2) spaces are skipped. What it does:
  size_t did = k < (l0 + 1) / 2 ? k : (l0 + 1) / 2;
  __CPROVER_assert(r == s + did && len == l0 - did, "skips min(k, ceil(len/2)) leading ' '");
#ifdef INTENDED
  __CPROVER_assert(r == s + k && len == l0 - k, "skips all leading ' ' (intended; fails)");
#endif
}
void h_replace_char(void) {
  size_t n;
  char *s = any_str(NB, &n);
  char before[NB + 1];
  for (size_t i = 0; i <= n; i++) before[i] = s[i];
  char f = nondet_char(), w = nondet_char();
  // the only call is '\t' -> ' '. With f == w it loops forever, with w == 0
  // it stops at the first replacement: both outside the domain.
  __CPROVER_assume(f != 0 && w != 0 && f != w);
  char *r = str_replace_char(s, f, w);
  __CPROVER_assert(r == s, "returns str");
  for (size_t i = 0; i <= n; i++)
    __CPROVER_assert(s[i] == (before[i] == f ? w : before[i]), "every find replaced, others kept");
}
// str_replace for its one call, str_replace(pattern, "\\ ", "\t"), and every
// pattern of length 0..SRB (the general rep/with search, and SRB = 6, run out
// of memory: the result's size depends on the input).
#ifndef SRB
#define SRB 4
#endif
void h_str_replace(void) {
  size_t n;
  char *o = any_str(SRB, &n);
  char rep[3] = "\\ ", with[2] = "\t";
  size_t lr = 2, lw = 1;
  char *r = str_replace(o, rep, with);
  // reference: scan left to right, replace each non-overlapping occurrence
  char want[SRB + 1];
  size_t w = 0, i = 0;
  while (i < n) {
    size_t j = 0;
    while (j < lr && i + j < n && o[i + j] == rep[j]) j++;
    if (j == lr) { for (size_t q = 0; q < lw; q++) want[w++] = with[q]; i += lr; }
    else want[w++] = o[i++];
  }
  want[w] = 0;
  __CPROVER_assert(r != NULL && __CPROVER_POINTER_OFFSET(r) == 0 && __CPROVER_OBJECT_SIZE(r) == w + 1, "fresh object of exact size");
  for (size_t q = 0; q <= w; q++) __CPROVER_assert(r[q] == want[q], "replaced text");
  free(r);
  char empty[1] = "";
  __CPROVER_assert(str_replace(o, empty, with) == NULL && str_replace(NULL, rep, with) == NULL, "NULL for an empty or NULL argument");
}

// ---- position arrays ----
static fzf_position_t *any_pos(uint32_t *old, size_t *osize, size_t max) {
  fzf_position_t *p = malloc(sizeof *p);
  p->cap = nondet_size();
  p->size = nondet_size();
  __CPROVER_assume(p->cap <= max && p->size <= p->cap);
  p->data = p->cap ? exact_malloc(p->cap, max, sizeof(uint32_t)) : NULL;
  for (size_t i = 0; i < p->size; i++) old[i] = p->data[i];
  *osize = p->size;
  return p;
}
void h_pos_array(void) {
  size_t n = any_len();
  fzf_position_t *p = fzf_pos_array(n);
  __CPROVER_assert(p->size == 0 && p->cap == n, "empty with capacity n");
  __CPROVER_assert(n == 0 ? p->data == NULL : __CPROVER_OBJECT_SIZE(p->data) == n * sizeof(uint32_t), "data");
  fzf_free_positions(p);
}
void h_append_pos(void) {
  uint32_t old[NB]; size_t os;
  fzf_position_t *p = any_pos(old, &os, NB);
  size_t v = nondet_size();
  __CPROVER_assume(v <= UINT32_MAX);
  append_pos(p, v);
  __CPROVER_assert(p->size == os + 1 && p->size <= p->cap, "one more");
  __CPROVER_assert(__CPROVER_OBJECT_SIZE(p->data) >= p->cap * sizeof(uint32_t), "cap is real");
  for (size_t i = 0; i < os; i++) __CPROVER_assert(p->data[i] == old[i], "old kept");
  __CPROVER_assert(p->data[os] == v, "appended");
  append_pos(NULL, v);   // no-op
}
void h_insert_range(void) {
  uint32_t old[NB]; size_t os;
  fzf_position_t *p = any_pos(old, &os, 3);   // capacity 0..3, then 0..4 positions added
  size_t s = nondet_size(), e = nondet_size();
  __CPROVER_assume(s <= INT32_MAX && e <= INT32_MAX && e <= s + 4);   // positions of a text < 2 GiB
  insert_range(p, s, e);
  size_t add = e > s ? e - s : 0;
  __CPROVER_assert(p->size == os + add && p->size <= p->cap, "size");
  __CPROVER_assert(__CPROVER_OBJECT_SIZE(p->data) >= p->cap * sizeof(uint32_t) || p->cap == 0, "cap is real");
  for (size_t i = 0; i < os; i++) __CPROVER_assert(p->data[i] == old[i], "old kept");
  for (size_t i = 0; i < add; i++) __CPROVER_assert(p->data[os + i] == s + i, "s..e-1 appended");
  insert_range(NULL, s, e);
}
void h_alloc(void) {
  fzf_slab_t *slab = NULL;
  if (nondet_bool()) {
    slab = malloc(sizeof *slab);
    slab->I16.cap = nondet_size(); slab->I32.cap = nondet_size();
    __CPROVER_assume(slab->I16.cap <= 2 * NB && slab->I32.cap <= 2 * NB);
    slab->I16.data = exact_malloc(slab->I16.cap, 2 * NB, sizeof(int16_t));
    slab->I32.data = exact_malloc(slab->I32.cap, 2 * NB, sizeof(int32_t));
  }
  size_t off16 = nondet_size(), off32 = nondet_size(), n = any_len();
  __CPROVER_assume(off16 <= 2 * NB && off32 <= 2 * NB);
  size_t o16 = off16, o32 = off32;
  fzf_i16_t a = alloc16(&off16, slab, n);
  fzf_i32_t b = alloc32(&off32, slab, n);
  if (slab && slab->I16.cap > o16 + n)
    __CPROVER_assert(!a.allocated && a.data == slab->I16.data + o16 && off16 == o16 + n, "16: slab slice");
  else {
    __CPROVER_assert(a.allocated && off16 == o16 && __CPROVER_OBJECT_SIZE(a.data) == n * 2, "16: fresh");
    for (size_t i = 0; i < n; i++) __CPROVER_assert(a.data[i] == 0, "16: zeroed");
  }
  __CPROVER_assert(a.size == n && a.cap == n, "16: size");
  if (slab && slab->I32.cap > o32 + n)
    __CPROVER_assert(!b.allocated && b.data == slab->I32.data + o32 && off32 == o32 + n, "32: slab slice");
  else {
    __CPROVER_assert(b.allocated && off32 == o32 && __CPROVER_OBJECT_SIZE(b.data) == n * 4, "32: fresh");
    for (size_t i = 0; i < n; i++) __CPROVER_assert(b.data[i] == 0, "32: zeroed");
  }
  __CPROVER_assert(b.size == n && b.cap == n, "32: size");
  free_alloc(a);
  free_alloc(b);
}

// ---- ascii_fuzzy_index / try_skip ----
// fzf's asciiFuzzyIndex: -1 unless every pattern byte occurs in order, where a
// lowercase pattern letter also matches its uppercase form when the search is
// case-insensitive; else the index just before the first byte's first
// occurrence (0 if it is at 0).
static bool r_hit(unsigned char c, unsigned char b, bool cs) {
  return c == b || (!cs && b >= 'a' && b <= 'z' && c == b - 32);
}
void h_ascii_fuzzy_index(void) {
  size_t n = any_len(), m = nondet_size();
  __CPROVER_assume(m <= 3);
  char *t = any_buf(n), *p = any_buf(m);
  bool cs = nondet_bool();
  fzf_string_t s = {t, n};
  int32_t r = ascii_fuzzy_index(&s, p, m, cs);
  size_t k = 0, first = n;
  for (size_t i = 0; i < n && k < m; i++)
    if (r_hit(U(t)[i], U(p)[k], cs)) { if (k == 0) first = i; k++; }
  if (k < m) __CPROVER_assert(r == -1, "no match");
  else if (m == 0) __CPROVER_assert(r == 0, "empty pattern");
  else __CPROVER_assert(r == (first > 0 ? (int32_t)first - 1 : 0), "index before first");
}
void h_try_skip(void) {
  size_t n = any_len();
  char *t = any_buf(n);
  bool cs = nondet_bool();
  char b = nondet_char();
  int32_t from = nondet_i32();
  __CPROVER_assume(0 <= from && (size_t)from <= n);
  fzf_string_t s = {t, n};
  int32_t r = try_skip(&s, cs, b, from);
  size_t want = n;
  for (size_t i = (size_t)from; i < n; i++) if (r_hit(U(t)[i], (unsigned char)b, cs)) { want = i; break; }
  __CPROVER_assert(r == (want == n ? -1 : (int32_t)want), "first hit at or after from");
}
