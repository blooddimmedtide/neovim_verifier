// libFuzzer harness for src/nvim/regexp.c (both engines) built with ASan + UBSan.
//
// Input: byte 0 = flags, then  pattern NUL subject NUL substitute.
//   flags bit 0: 'magic'          bit 1: ignore case
//   flags bit 2: RE_STRICT        bit 3: also run vim_regexec_multi on a buffer
//   flags bits 4-5: start column (0..3, clamped to the subject length)
// Checks:
//   1. no sanitizer report in compile, match or substitute (both engines);
//   2. the backtracking engine (1) and the NFA engine (2) agree on whether the
//      pattern matches and on every sub-match position (when both compile);
//   3. vim_regsub's length pass equals the bytes its copy pass writes, and the
//      copy pass stays inside a buffer of exactly that size.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "nvim/buffer.h"
#include "nvim/event/loop.h"
#include "nvim/globals.h"
#include "nvim/main.h"
#include "nvim/mbyte.h"
#include "nvim/memline.h"
#include "nvim/memory.h"
#include "nvim/option_vars.h"
#include "nvim/profile.h"
#include "nvim/regexp.h"
#include "nvim/regexp_defs.h"

void event_init(void);
void fuzz_early_init(void);

static int diff_mode = 1;
static int skip_composing = 0;  // FUZZ_SKIP_COMPOSING: no differential on composing chars (known finding)

// Strict UTF-8 (RFC 3629): the engines are only compared on valid text.
static int valid_utf8(const char *s)
{
  const uint8_t *p = (const uint8_t *)s;
  while (*p) {
    uint32_t c;
    int n;
    if (*p < 0x80) {
      p++;
      continue;
    } else if ((*p & 0xE0) == 0xC0) {
      c = *p & 0x1F; n = 1;
    } else if ((*p & 0xF0) == 0xE0) {
      c = *p & 0x0F; n = 2;
    } else if ((*p & 0xF8) == 0xF0) {
      c = *p & 0x07; n = 3;
    } else {
      return 0;
    }
    for (int i = 1; i <= n; i++) {
      if ((p[i] & 0xC0) != 0x80) {
        return 0;
      }
      c = (c << 6) | (p[i] & 0x3F);
    }
    if ((n == 1 && c < 0x80) || (n == 2 && c < 0x800) || (n == 3 && c < 0x10000)
        || c > 0x10FFFF || (c >= 0xD800 && c <= 0xDFFF)) {
      return 0;
    }
    p += n + 1;
  }
  return 1;
}

// FUZZ_SKIP_LONGNUM: skip patterns with 19+ digit runs (known finding: getdecchrs overflow).
static int skip_longnum = 0;
static int has_longnum(const char *s)
{
  int run = 0;
  for (; *s; s++) {
    run = (*s >= '0' && *s <= '9') ? run + 1 : 0;
    if (run >= 19) {
      return 1;
    }
  }
  return 0;
}

// FUZZ_SKIP_BSMB: no differential when a backslash precedes a non-ASCII byte (known NFA finding).
static int skip_bsmb = 0;
static int has_bsmb(const char *s)
{
  for (; *s; s++) {
    if (s[0] == '\\' && (uint8_t)s[1] >= 0x80) {
      return 1;
    }
    if (s[0] == '\\' && s[1] != NUL) {
      s++;
    }
  }
  return 0;
}

static int has_composing(const char *s)
{
  for (const char *p = s; *p; p += utf_ptr2len(p)) {
    if (utf_iscomposing_legacy(utf_ptr2char(p))) {
      return 1;
    }
  }
  return 0;
}

int LLVMFuzzerInitialize(int *argc, char ***argv)
{
  (void)argc; (void)argv;
  event_init();
  fuzz_early_init();
  emsg_silent = 1;
  if (getenv("FUZZ_SKIP_COMPOSING")) {
    skip_composing = 1;
  }
  if (getenv("FUZZ_SKIP_LONGNUM")) {
    skip_longnum = 1;
  }
  if (getenv("FUZZ_SKIP_BSMB")) {
    skip_bsmb = 1;
  }
  if (getenv("FUZZ_NO_DIFF")) {
    diff_mode = 0;
  }
  return 0;
}

static char *take(const uint8_t **d, size_t *n)
{
  const uint8_t *z = memchr(*d, 0, *n);
  size_t len = z ? (size_t)(z - *d) : *n;
  char *s = xmalloc(len + 1);
  memcpy(s, *d, len);
  s[len] = NUL;
  *d += z ? len + 1 : len;
  *n -= z ? len + 1 : len;
  return s;
}

typedef struct {
  int compiled, matched;
  long s[NSUBEXP], e[NSUBEXP];
} res_T;

static void run_engine(int engine, const char *pat, const char *subj, const char *sub, int fl,
                       res_T *r)
{
  memset(r, 0, sizeof *r);
  p_re = engine;
  int re_flags = RE_STRING | ((fl & 1) ? RE_MAGIC : 0) | ((fl & 4) ? RE_STRICT : 0);
  regmatch_T rm = { 0 };
  rm.regprog = vim_regcomp(pat, re_flags);
  if (rm.regprog == NULL) {
    return;
  }
  r->compiled = 1;
  rm.rm_ic = (fl & 2) != 0;
  colnr_T col = (colnr_T)((fl >> 4) & 3);
  size_t sl = strlen(subj);
  if ((size_t)col > sl) {
    col = (colnr_T)sl;
  }
  r->matched = vim_regexec_nl(&rm, subj, col);
  if (r->matched) {
    for (int i = 0; i < NSUBEXP; i++) {
      r->s[i] = rm.startp[i] ? (long)(rm.startp[i] - subj) : -1;
      r->e[i] = rm.endp[i] ? (long)(rm.endp[i] - subj) : -1;
    }
    if (sub[0] != NUL && !(sub[0] == '\\' && sub[1] == '=') && rm.regprog != NULL) {
      int flags = (fl & 1) ? REGSUB_MAGIC : 0;
      char dummy[1];
      int len = vim_regsub(&rm, (char *)sub, NULL, dummy, 0, flags);
      if (len > 0) {
        char *dest = xmalloc((size_t)len);
        int len2 = vim_regsub(&rm, (char *)sub, NULL, dest, len, flags | REGSUB_COPY);
        if (len2 > len || strlen(dest) + 1 > (size_t)len) {
          fprintf(stderr, "regsub length mismatch: %d then %d (strlen %zu)\n", len, len2,
                  strlen(dest));
          abort();
        }
        xfree(dest);
      }
    }
  }
  if (rm.regprog != NULL && (fl & 8)) {
    // Multi-line match over the subject split into buffer lines.
    regmmatch_T mm = { 0 };
    mm.regprog = rm.regprog;
    rm.regprog = NULL;
    mm.rmm_ic = (fl & 2) != 0;
    mm.rmm_maxcol = 0;
    proftime_T tm = profile_setlimit(200);
    int timed_out = 0;
    for (linenr_T l = 1; l <= curbuf->b_ml.ml_line_count && mm.regprog != NULL; l++) {
      (void)vim_regexec_multi(&mm, curwin, curbuf, l, 0, &tm, &timed_out);
      if (timed_out) {
        break;
      }
    }
    vim_regfree(mm.regprog);
  }
  vim_regfree(rm.regprog);
}

static void load_buffer(const char *subj)
{
  // Replace the buffer contents with the subject's lines.
  while (curbuf->b_ml.ml_line_count > 1) {
    ml_delete(1);
  }
  ml_replace(1, "", true);
  const char *p = subj;
  linenr_T l = 0;
  while (true) {
    const char *nl = strchr(p, '\n');
    size_t len = nl ? (size_t)(nl - p) : strlen(p);
    char *line = xmemdupz(p, len);
    if (l == 0) {
      ml_replace(1, line, false);
    } else {
      ml_append(l, line, 0, false);
      xfree(line);
    }
    l++;
    if (!nl) {
      break;
    }
    p = nl + 1;
  }
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
  if (size < 1 || size > 4096) {
    return 0;
  }
  int fl = data[0];
  data++; size--;
  char *pat = take(&data, &size);
  char *subj = take(&data, &size);
  char *sub = take(&data, &size);
  if (skip_longnum && has_longnum(pat)) {
    xfree(pat);
    xfree(subj);
    xfree(sub);
    return -1;  // keep out of the corpus
  }
  if (fl & 8) {
    load_buffer(subj);
  }
  res_T bt, nfa;
  run_engine(1, pat, subj, sub, fl, &bt);
  run_engine(2, pat, subj, sub, fl, &nfa);
  if (diff_mode && bt.compiled && nfa.compiled && valid_utf8(pat) && valid_utf8(subj)
      && !(skip_composing && (has_composing(pat) || has_composing(subj)))
      && !(skip_bsmb && has_bsmb(pat))) {
    int bad = bt.matched != nfa.matched;
    for (int i = 0; !bad && bt.matched && i < NSUBEXP; i++) {
      bad = bt.s[i] != nfa.s[i] || bt.e[i] != nfa.e[i];
    }
    if (bad) {
      fprintf(stderr, "ENGINE MISMATCH pat=[%s] subj=[%s] flags=%d bt=%d nfa=%d\n", pat, subj,
              fl, bt.matched, nfa.matched);
      for (int i = 0; i < NSUBEXP; i++) {
        fprintf(stderr, "  %d: bt %ld-%ld nfa %ld-%ld\n", i, bt.s[i], bt.e[i], nfa.s[i], nfa.e[i]);
      }
      abort();
    }
  }
  p_re = 0;
  xfree(pat);
  xfree(subj);
  xfree(sub);
  return 0;
}
