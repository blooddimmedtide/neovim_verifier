// Reference parser for fzf_parse_pattern (fzf's extended-search syntax).
// Needs fzf.h's fzf_case_types and spec.h. PL bounds the pattern length.
#ifndef FZF_SPEC_PARSE_H
#define FZF_SPEC_PARSE_H
#include "spec.h"
// ---- reference parser, from fzf's extended-search syntax (README "Search
// syntax" and fzf's pattern.go) as this port documents it ----
enum { A_V2, A_EXACT, A_PREFIX, A_SUFFIX, A_EQUAL };
typedef struct { int fn; bool inv, cs; char text[PL + 1]; size_t len; } rterm;
typedef struct { rterm t[MAXT]; size_t n; } rset;
typedef struct { rset s[MAXT]; size_t n; bool only_inv; } rpat;

static inline void ref_parse(const char *in, size_t n, int mode, bool fuzzy, rpat *out) {
  out->n = 0;
  // 1. drop leading spaces; drop trailing spaces unless escaped as "\ ".
  size_t a = 0, b = n;
  while (a < b && in[a] == ' ') a++;
  while (b > a && in[b - 1] == ' ' && !(b - a >= 2 && in[b - 2] == '\\')) b--;
  // 2. "\ " is a literal space; unescaped spaces separate tokens.
  char tok[PL + 1]; size_t tl = 0;
  rset cur; cur.n = 0;
  bool switch_set = false, after_bar = false;
  for (size_t i = a; i <= b; i++) {
    bool esc = i + 1 < b && in[i] == '\\' && in[i + 1] == ' ';
    if (i < b && (esc || in[i] != ' ')) {
      // the port marks "\ " with a TAB and turns every TAB of a token into a
      // space, so a TAB typed in the pattern also searches for a space (fzf
      // itself keeps it; findings/observations.md)
      tok[tl++] = (esc || in[i] == '\t') ? ' ' : in[i];
      if (esc) i++;
      continue;
    }
    if (tl == 0) continue;   // between separators
    tok[tl] = 0;
    // 3. one token: case mode, then the operators
    char t[PL + 1]; bool cs = false;
    for (size_t k = 0; k <= tl; k++) {
      t[k] = (char)r_fold((unsigned char)tok[k], false);
      if (t[k] != tok[k]) cs = true;   // has an uppercase letter
    }
    cs = mode == CaseRespect || (mode == CaseSmart && cs);
    if (cs) for (size_t k = 0; k <= tl; k++) t[k] = tok[k];
    size_t len = tl; tl = 0;
    char *p = t;
    if (cur.n > 0 && !after_bar && len == 1 && p[0] == '|') {   // OR with the previous term
      switch_set = false; after_bar = true;
      continue;
    }
    after_bar = false;
    int fn = fuzzy ? A_V2 : A_EXACT;
    bool inv = false;
    if (len > 0 && p[0] == '!') { inv = true; fn = A_EXACT; p++; len--; }
    if (!(len == 1 && p[0] == '$') && len > 0 && p[len - 1] == '$') { fn = A_SUFFIX; p[--len] = 0; }
    if (len > 0 && p[0] == '\'') { fn = (fuzzy && !inv) ? A_EXACT : A_V2; p++; len--; }
    else if (len > 0 && p[0] == '^') { fn = fn == A_SUFFIX ? A_EQUAL : A_PREFIX; p++; len--; }
    if (len == 0) continue;
    if (switch_set) { out->s[out->n++] = cur; cur.n = 0; }
    rterm *r = &cur.t[cur.n++];
    r->fn = fn; r->inv = inv; r->cs = cs; r->len = len;
    for (size_t k = 0; k <= len; k++) r->text[k] = p[k];
    switch_set = true;
  }
  if (cur.n > 0) out->s[out->n++] = cur;
  bool only = true;
  for (size_t i = 0; i < out->n; i++)
    if (out->s[i].n > 1 || !out->s[i].t[0].inv) only = false;
  out->only_inv = only;
}
#endif
