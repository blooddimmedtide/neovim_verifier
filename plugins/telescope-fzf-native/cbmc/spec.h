// Reference specification for telescope-fzf-native's src/fzf.c, written from
// fzf's algorithm (junegunn/fzf src/algo/algo.go, the version the C file is a
// port of) and the plugin's documentation, NOT from the C code's helpers. All
// byte values are handled as unsigned char; case folding and whitespace are the
// "C" locale (only A-Z fold; space, \t \n \v \f \r are white).
//
// Sizes are bounded only by the harness; these functions have no bound.
#ifndef FZF_SPEC_H
#define FZF_SPEC_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Scoring constants of fzf (algo.go): a match is worth 16, a gap costs 3 to
// open and 1 per further character; a word boundary or a non-word character is
// worth 8 (half a match), a camelCase or letter->digit change 7 (boundary minus
// one gap step), a consecutive character at least 4, the first pattern
// character's bonus counts twice.
#define R_MATCH 16
#define R_GAP_START (-3)
#define R_GAP_EXT (-1)
#define R_BOUNDARY 8
#define R_NONWORD 8
#define R_CAMEL 7
#define R_CONSEC 4

// Character classes, numbered as fzf.c's char_types documents them.
#define RC_NONWORD 0
#define RC_LOWER 1
#define RC_UPPER 2
#define RC_NUMBER 4

static inline bool r_space(unsigned char c) {
  return c == 0x20 || (c >= 0x09 && c <= 0x0d);   // " \t\n\v\f\r"
}
static inline unsigned char r_fold(unsigned char c, bool cs) {
  return (!cs && c >= 0x41 && c <= 0x5a) ? (unsigned char)(c + 0x20) : c;
}
static inline int r_class(unsigned char c) {
  if (c >= 0x61 && c <= 0x7a) return RC_LOWER;
  if (c >= 0x41 && c <= 0x5a) return RC_UPPER;
  if (c >= 0x30 && c <= 0x39) return RC_NUMBER;
  return RC_NONWORD;   // also every byte >= 0x80: fzf.c only knows ASCII
}
static inline bool r_word(int cls) { return cls != RC_NONWORD; }
// fzf's bonusFor: entering a word after a non-word char is a boundary;
// lower->Upper and non-digit->digit are camel/123 changes; a non-word
// character itself gets the non-word bonus.
static inline int r_bonus(int prev, int cur) {
  if (!r_word(prev) && r_word(cur)) return R_BOUNDARY;
  if ((prev == RC_LOWER && cur == RC_UPPER) || (prev != RC_NUMBER && cur == RC_NUMBER))
    return R_CAMEL;
  if (!r_word(cur)) return R_NONWORD;
  return 0;
}
// The bonus of position i of t: the start of the text counts as a boundary.
static inline int r_bonus_at(const unsigned char *t, size_t i) {
  return i == 0 ? R_BOUNDARY : r_bonus(r_class(t[i - 1]), r_class(t[i]));
}
static inline int r_max(int a, int b) { return a > b ? a : b; }

// Is p[0..m) a subsequence of fold(t[a..b))?
static inline bool r_subseq(const unsigned char *t, size_t a, size_t b,
                            const unsigned char *p, size_t m, bool cs) {
  size_t k = 0;
  for (size_t i = a; i < b && k < m; i++)
    if (r_fold(t[i], cs) == p[k]) k++;
  return k == m;
}

// fzf's calculateScore for the window [s, e) of t, matched against p[0..m).
// The matched positions are the leftmost occurrence of p in the window
// (written to pos[0..m-1]); the caller guarantees the window holds p as a
// subsequence whose leftmost occurrence ends at e - 1.
// Score: every matched char 16 + its bonus (the first pattern char's bonus
// twice); every maximal run of L unmatched chars -3 - (L - 1). The bonus of a
// matched char is its own bonus at the start of a run of consecutive matched
// chars ("chunk"); inside a chunk it is the largest of its own bonus, 4, the
// chunk's first bonus, and 8 if any char of the chunk after the first had a
// boundary bonus (fzf: a chunk keeps the bonus of its start, and a boundary
// inside it raises that).
static inline int32_t r_score(const unsigned char *t, size_t s, size_t e,
                              const unsigned char *p, size_t m, bool cs, size_t *pos) {
  size_t k = 0;
  for (size_t i = s; i < e && k < m; i++)
    if (r_fold(t[i], cs) == p[k]) pos[k++] = i;
  int32_t score = 0;
  for (size_t i = s; i < e; i++) {
    size_t kk = m;
    for (size_t j = 0; j < m; j++) if (pos[j] == i) kk = j;
    if (kk == m) {   // unmatched: opens a gap or extends one
      // a gap opens when the previous char of the window was matched (or i == s)
      bool prev_matched = false;
      if (i > s) for (size_t j = 0; j < m; j++) if (pos[j] == i - 1) prev_matched = true;
      bool open = (i == s) || prev_matched;
      score += open ? R_GAP_START : R_GAP_EXT;
      continue;
    }
    // chunk start c0: walk back over matched chars inside the window
    size_t c0 = i;
    bool inner_boundary = false;
    for (;;) {
      if (c0 == s) break;
      bool m_prev = false;
      for (size_t j = 0; j < m; j++) if (pos[j] == c0 - 1) m_prev = true;
      if (!m_prev) break;
      if (r_bonus_at(t, c0) == R_BOUNDARY) inner_boundary = true;   // chars c0..i after the start
      c0--;
    }
    int raw = r_bonus_at(t, i);
    int b = raw;
    if (c0 != i) {
      b = r_max(r_max(raw, R_CONSEC), r_bonus_at(t, c0));
      if (inner_boundary) b = r_max(b, R_BOUNDARY);
    }
    score += R_MATCH + (kk == 0 ? 2 * b : b);
  }
  return score;
}

typedef struct { int32_t start, end, score; } r_result;
#define R_NOMATCH ((r_result){-1, -1, 0})

// ---- references written from fzf's definitions ----
static inline size_t lead_ws(const unsigned char *t, size_t n) { size_t k = 0; while (k < n && r_space(t[k])) k++; return k; }
static inline size_t trail_ws(const unsigned char *t, size_t n) { size_t k = 0; while (k < n && r_space(t[n - 1 - k])) k++; return k; }
static inline bool window_eq(const unsigned char *t, size_t a, const unsigned char *p, size_t m, bool cs) {
  for (size_t i = 0; i < m; i++) if (r_fold(t[a + i], cs) != p[i]) return false;
  return true;
}
static inline r_result window_result(const unsigned char *t, size_t a, const unsigned char *p, size_t m, bool cs, size_t *pos) {
  int32_t sc = r_score(t, a, a + m, p, m, cs, pos);
  return (r_result){(int32_t)a, (int32_t)(a + m), sc};
}

// PrefixMatch: the pattern at the start of the text, after the text's
// leading whitespace unless the pattern itself starts with whitespace.
static inline r_result ref_prefix(const unsigned char *t, size_t n, const unsigned char *p, size_t m, bool cs, size_t *pos, size_t *k) {
  *k = 0;
  if (m == 0) return (r_result){0, 0, 0};
  size_t a = r_space(p[0]) ? 0 : lead_ws(t, n);
  if (n - a < m || !window_eq(t, a, p, m, cs)) return R_NOMATCH;
  *k = m;
  return window_result(t, a, p, m, cs, pos);
}
// SuffixMatch: the pattern at the end of the text, before its trailing
// whitespace unless the pattern ends with whitespace. Empty pattern: the
// (empty) match at the end of the trimmed text.
static inline r_result ref_suffix(const unsigned char *t, size_t n, const unsigned char *p, size_t m, bool cs, size_t *pos, size_t *k) {
  *k = 0;
  size_t e = (m == 0 || !r_space(p[m - 1])) ? n - trail_ws(t, n) : n;
  if (m == 0) return (r_result){(int32_t)e, (int32_t)e, 0};
  if (e < m || !window_eq(t, e - m, p, m, cs)) return R_NOMATCH;
  *k = m;
  return window_result(t, e - m, p, m, cs, pos);
}
// EqualMatch (as this port defines it): the text is the pattern surrounded by
// whitespace only; the score is a fixed function of the pattern length.
static inline r_result ref_equal(const unsigned char *t, size_t n, const unsigned char *p, size_t m, bool cs, size_t *pos, size_t *k) {
  *k = 0;
  if (m == 0) return R_NOMATCH;
  size_t l = lead_ws(t, n), r = trail_ws(t, n);
  if (l + r >= n || n - l - r != m || !window_eq(t, l, p, m, cs)) return R_NOMATCH;   // all-white text never matches m > 0
  *k = m;
  for (size_t i = 0; i < m; i++) pos[i] = l + i;
  return (r_result){(int32_t)l, (int32_t)(l + m), (int32_t)((R_MATCH + R_BOUNDARY) * m + R_BOUNDARY)};
}
// ExactMatchNaive: among all places where the pattern occurs as a substring,
// the one whose first char has the highest bonus, the earliest of those.
static inline r_result ref_exact(const unsigned char *t, size_t n, const unsigned char *p, size_t m, bool cs, size_t *pos, size_t *k) {
  *k = 0;
  if (m == 0) return (r_result){0, 0, 0};
  size_t best = n; int bb = -1;
  for (size_t a = 0; a + m <= n; a++)
    if (window_eq(t, a, p, m, cs) && r_bonus_at(t, a) > bb) { best = a; bb = r_bonus_at(t, a); }
  if (best == n) return R_NOMATCH;
  *k = m;
  return window_result(t, best, p, m, cs, pos);
}
// FuzzyMatchV1: the shortest prefix of the text that contains the pattern as
// a subsequence ends at `end`; `start` is the latest start from which
// [start, end) still contains it; scored with calculateScore.
static inline r_result ref_v1(const unsigned char *t, size_t n, const unsigned char *p, size_t m, bool cs, size_t *pos, size_t *k) {
  *k = 0;
  if (m == 0) return (r_result){0, 0, 0};
  size_t e = 0;
  while (e <= n && !r_subseq(t, 0, e, p, m, cs)) e++;
  if (e > n) return R_NOMATCH;
  size_t s = e;
  while (!r_subseq(t, s, e, p, m, cs)) s--;   // terminates: s = 0 works
  *k = m;
  return (r_result){(int32_t)s, (int32_t)e, r_score(t, s, e, p, m, cs, pos)};
}

// fzf's asciiFuzzyIndex / trySkip (algo.go 0.27.0), on bytes: -1 unless the
// pattern occurs in order (a lowercase pattern letter also matching its
// uppercase form when case-insensitive); else one before the first byte's
// first occurrence (0 if that is 0).
static inline bool r_hit(unsigned char c, unsigned char b, bool cs) {
  return c == b || (!cs && b >= 'a' && b <= 'z' && c == b - 32);
}
static inline long r_ascii_fuzzy_index(const unsigned char *t, size_t n, const unsigned char *p, size_t m, bool cs) {
  size_t k = 0, first = 0;
  for (size_t i = 0; i < n && k < m; i++)
    if (r_hit(t[i], p[k], cs)) { if (k == 0) first = i; k++; }
  if (k < m) return -1;
  return (m > 0 && first > 0) ? (long)first - 1 : 0;
}
static inline int16_t r_max16(int16_t a, int16_t b) { return a > b ? a : b; }
#ifndef RV2_N
#define RV2_N 64
#endif
#ifndef RV2_M
#define RV2_M 16
#endif

// FuzzyMatchV2, transcribed from fzf 0.27.0 algo.go (forward = true,
// withPos = true) to bytes, as this port defines bytes (classes and case
// folding ASCII only; normalize is the identity), with every matrix
// zero-initialized (what Go's alloc16 gives without a slab). This is a second
// implementation of fzf's DP, so it shows the port computes what fzf computes,
// not that fzf's alignment is optimal. pos gets the positions in the order fzf
// appends them (last pattern byte first).
static inline r_result ref_v2(const unsigned char *t, size_t n, const unsigned char *p, size_t m, bool cs, size_t *pos, size_t *k) {
  *k = 0;
  if (m == 0) return (r_result){0, 0, 0};
  long fi = r_ascii_fuzzy_index(t, n, p, m, cs);
  if (fi < 0) return R_NOMATCH;
  size_t idx = (size_t)fi;
  // fixed-size buffers (CBMC handles symbolic-size arrays badly); the caller's
  // bound RV2_N must cover the text, RV2_M the pattern
  int16_t H0[RV2_N], C0[RV2_N], B[RV2_N]; size_t F[RV2_M]; unsigned char T[RV2_N];
  if (n > RV2_N || m > RV2_M) return (r_result){-2, -2, -2};   // never equal to a real result
  for (size_t i = 0; i < n; i++) { H0[i] = 0; C0[i] = 0; B[i] = 0; T[i] = t[i]; }
  for (size_t i = 0; i < m; i++) F[i] = 0;
  int16_t maxScore = 0; size_t maxScorePos = 0, pidx = 0, lastIdx = 0;
  unsigned char pchar0 = p[0], pchar = p[0];
  int16_t prevH0 = 0; int prevClass = RC_NONWORD; bool inGap = false;
  for (size_t col = idx; col < n; col++) {
    unsigned char ch = T[col];
    int cls = r_class(ch);
    if (!cs && cls == RC_UPPER) ch = (unsigned char)(ch + 32);
    T[col] = ch;
    int16_t bonus = (int16_t)r_bonus(prevClass, cls);
    B[col] = bonus; prevClass = cls;
    if (ch == pchar) {
      if (pidx < m) { F[pidx] = col; pidx++; pchar = p[pidx < m - 1 ? pidx : m - 1]; }
      lastIdx = col;
    }
    if (ch == pchar0) {
      int16_t score = (int16_t)(R_MATCH + bonus * 2);
      H0[col] = score; C0[col] = 1;
      if (m == 1 && score > maxScore) {
        maxScore = score; maxScorePos = col;
        if (bonus == R_BOUNDARY) break;
      }
      inGap = false;
    } else {
      H0[col] = r_max16((int16_t)(prevH0 + (inGap ? R_GAP_EXT : R_GAP_START)), 0);
      C0[col] = 0; inGap = true;
    }
    prevH0 = H0[col];
  }
  if (pidx != m) return R_NOMATCH;
  if (m == 1) { pos[0] = maxScorePos; *k = 1; return (r_result){(int32_t)maxScorePos, (int32_t)maxScorePos + 1, maxScore}; }
  size_t f0 = F[0], width = lastIdx - f0 + 1;
  int16_t H[RV2_N * RV2_M], C[RV2_N * RV2_M];
  for (size_t i = 0; i < width * m; i++) { H[i] = 0; C[i] = 0; }
  for (size_t i = 0; i < width; i++) { H[i] = H0[f0 + i]; C[i] = C0[f0 + i]; }
  for (size_t r = 1; r < m; r++) {
    size_t f = F[r]; unsigned char pc = p[r]; size_t row = r * width;
    bool gap = false;
    H[row + f - f0 - 1] = 0;   // Hleft[0] = 0
    for (size_t col = f; col <= lastIdx; col++) {
      size_t j0 = col - f0;
      int16_t s1 = 0, s2 = 0, consecutive = 0;
      s2 = (int16_t)(H[row + j0 - 1] + (gap ? R_GAP_EXT : R_GAP_START));
      if (pc == T[col]) {
        s1 = (int16_t)(H[row - width + j0 - 1] + R_MATCH);
        int16_t b = B[col];
        consecutive = (int16_t)(C[row - width + j0 - 1] + 1);
        if (b == R_BOUNDARY) consecutive = 1;
        else if (consecutive > 1) b = r_max16(b, r_max16(R_CONSEC, B[col - (size_t)consecutive + 1]));
        if (s1 + b < s2) { s1 = (int16_t)(s1 + B[col]); consecutive = 0; }
        else s1 = (int16_t)(s1 + b);
      }
      C[row + j0] = consecutive;
      gap = s1 < s2;
      int16_t score = r_max16(r_max16(s1, s2), 0);
      if (r == m - 1 && score > maxScore) { maxScore = score; maxScorePos = col; }
      H[row + j0] = score;
    }
  }
  size_t i = m - 1, j = maxScorePos;
  bool preferMatch = true;
  for (;;) {
    size_t I = i * width, j0 = j - f0;
    int16_t s = H[I + j0], s1 = 0, s2 = 0;
    if (i > 0 && j >= F[i]) s1 = H[I - width + j0 - 1];
    if (j > F[i]) s2 = H[I + j0 - 1];
    if (s > s1 && (s > s2 || (s == s2 && preferMatch))) {
      pos[(*k)++] = j;
      if (i == 0) break;
      i--;
    }
    preferMatch = C[I + j0] > 1 || (I + width + j0 + 1 < width * m && C[I + width + j0 + 1] > 0);
    j--;
  }
  return (r_result){(int32_t)j, (int32_t)maxScorePos + 1, maxScore};
}

#endif
