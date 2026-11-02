// libFuzzer harness for src/nvim/search.c and src/nvim/fuzzy.c, built with ASan + UBSan.
//
// Input: byte 0 = flags, byte 1 = cursor selector, then  pattern NUL buffer-text.
// The buffer text is split on '\n' into buffer lines.
// Calls: searchit (both directions, several option sets), findmatchlimit (every
// brace/comment kind), search_for_exact_line, fuzzy_match, fuzzy_match_str,
// fuzzy_match_str_with_pos, search_for_fuzzy_match, pat_has_uppercase, ignorecase_opt.
// Checks: no sanitizer report; every returned position lies inside the buffer
// (line in 1..line_count, column <= line length); fuzzy match positions are
// strictly increasing character indexes below the subject's character count.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "nvim/buffer.h"
#include "nvim/buffer_defs.h"
#include "nvim/fuzzy.h"
#include "nvim/garray.h"
#include "nvim/globals.h"
#include "nvim/mbyte.h"
#include "nvim/memline.h"
#include "nvim/memory.h"
#include "nvim/option_vars.h"
#include "nvim/profile.h"
#include "nvim/search.h"

void fuzz_early_init(void);
void event_init(void);

int LLVMFuzzerInitialize(int *argc, char ***argv)
{
  (void)argc; (void)argv;
  event_init();
  fuzz_early_init();
  emsg_silent = 1;
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

static void load_buffer(const char *text)
{
  while (curbuf->b_ml.ml_line_count > 1) {
    ml_delete(1);
  }
  ml_replace(1, "", true);
  const char *p = text;
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

static void check_pos(const char *what, pos_T p)
{
  // An exclusive end may sit just past the last line's newline: (line_count + 1, 0).
  if (p.lnum == curbuf->b_ml.ml_line_count + 1 && p.col == 0 && strstr(what, "end")) {
    return;
  }
  if (p.lnum < 1 || p.lnum > curbuf->b_ml.ml_line_count) {
    fprintf(stderr, "%s: line %d outside 1..%d\n", what, (int)p.lnum,
            (int)curbuf->b_ml.ml_line_count);
    abort();
  }
  size_t len = strlen(ml_get(p.lnum));
  if (p.col < 0 || (size_t)p.col > len) {
    fprintf(stderr, "%s: col %d outside 0..%zu (line %d)\n", what, (int)p.col, len, (int)p.lnum);
    abort();
  }
}

// Positions are character indexes into "str", strictly increasing within each
// pattern word (words are split on white space unless "matchseq").
static void check_fuzzy_positions(const char *str, const char *pat, bool matchseq,
                                  const uint32_t *m, int n)
{
  int chars = mb_charlen(str);
  int k = 0;
  bool new_word = true;
  for (const char *p = pat; *p != NUL && k < n; MB_PTR_ADV(p)) {
    if (!matchseq && ascii_iswhite(utf_ptr2char(p))) {
      new_word = true;
      continue;
    }
    if (m[k] >= (uint32_t)chars || (!new_word && m[k] <= m[k - 1])) {
      fprintf(stderr, "fuzzy position %d = %u bad (chars %d)\n", k, m[k], chars);
      abort();
    }
    new_word = false;
    k++;
  }
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
  if (size < 2 || size > 4096) {
    return 0;
  }
  int fl = data[0];
  int sel = data[1];
  data += 2; size -= 2;
  char *pat = take(&data, &size);
  char *text = take(&data, &size);
  load_buffer(text);

  linenr_T nlines = curbuf->b_ml.ml_line_count;
  linenr_T lnum = 1 + (linenr_T)((sel & 0x0f) % nlines);
  size_t llen = strlen(ml_get(lnum));
  colnr_T col = (colnr_T)(((size_t)(sel >> 4)) % (llen + 1));
  curwin->w_cursor.lnum = lnum;
  curwin->w_cursor.col = col;
  curwin->w_cursor.coladd = 0;
  p_ic = (fl & 1) != 0;
  p_scs = (fl & 2) != 0;
  p_ws = (fl & 4) != 0;

  // searchit, forward and backward.
  if (pat[0] != NUL && !(pat[0] == '\\' && pat[1] == '=')) {
    static const int optsets[] = { 0, SEARCH_END, SEARCH_START, SEARCH_COL | SEARCH_END };
    for (int dirn = 0; dirn < 2; dirn++) {
      for (int k = 0; k < 4; k++) {
        pos_T pos = curwin->w_cursor;
        pos_T end_pos = { 0 };
        proftime_T tm = profile_setlimit(100);
        searchit_arg_T sia = { .sa_tm = &tm };
        int count = 1 + ((fl >> 4) & 3);
        int r = searchit(curwin, curbuf, &pos, &end_pos, dirn ? BACKWARD : FORWARD, pat,
                         strlen(pat), count, optsets[k] | SEARCH_KEEP, RE_SEARCH,
                         (fl & 0x40) == 0, &sia);
        if (r != FAIL && !sia.sa_timed_out) {
          check_pos("searchit pos", pos);
          if (end_pos.lnum != 0) {
            check_pos("searchit end_pos", end_pos);
          }
        }
      }
    }
    pos_T epos = curwin->w_cursor;
    if (search_for_exact_line(curbuf, &epos, (fl & 0x80) ? BACKWARD : FORWARD, pat) == OK) {
      check_pos("search_for_exact_line", epos);
    }
    (void)pat_has_uppercase(pat);
    (void)ignorecase_opt(pat, true, true);
  }

  // findmatchlimit for every kind of match it supports.
  static const int initcs[] = { 0, '(', ')', '{', '}', '[', ']', '*', '/', '#', 'R' };
  for (size_t i = 0; i < sizeof initcs / sizeof initcs[0]; i++) {
    for (int f = 0; f < 4; f++) {
      int flags = (f & 1 ? FM_BACKWARD : FM_FORWARD) | (f & 2 ? FM_SKIPCOMM : 0);
      if ((fl & 0x80) && initcs[i] == '{') {
        flags |= FM_BLOCKSTOP;
      }
      curwin->w_cursor.lnum = lnum;
      curwin->w_cursor.col = col;
      pos_T *mp = findmatchlimit(NULL, initcs[i], flags, (fl & 0x40) ? 3 : 0);
      if (mp != NULL) {
        check_pos("findmatchlimit", *mp);
      }
    }
  }
  curwin->w_cursor.lnum = lnum;
  curwin->w_cursor.col = col;

  // fuzzy matching against every line.
  for (linenr_T l = 1; l <= nlines; l++) {
    char *line = ml_get(l);
    int score = 0;
    uint32_t matches[FUZZY_MATCH_MAX_LEN];
    int maxm = (fl & 0x20) ? 3 : FUZZY_MATCH_MAX_LEN;
    char *linecopy = xstrdup(line);
    if (fuzzy_match(linecopy, pat, (fl & 0x10) != 0, &score, matches, maxm)) {
      int npat = 0;
      for (const char *p = pat; *p != NUL; MB_PTR_ADV(p)) {
        if (!ascii_iswhite(utf_ptr2char(p))) {
          npat++;
        }
      }
      if ((fl & 0x10) == 0 && npat <= maxm) {
        check_fuzzy_positions(linecopy, pat, false, matches, npat);
      }
    }
    (void)fuzzy_match_str(linecopy, pat);
    garray_T *gap = fuzzy_match_str_with_pos(linecopy, pat);
    if (gap != NULL) {
      check_fuzzy_positions(linecopy, pat, false, (uint32_t *)gap->ga_data, gap->ga_len);
      ga_clear(gap);
      xfree(gap);
    }
    xfree(linecopy);
  }
  if (pat[0] != NUL) {
    pos_T pos = curwin->w_cursor;
    pos_T start_pos = pos;
    int len = 0;
    char *ptr = NULL;
    int score = 0;
    if (search_for_fuzzy_match(curbuf, &pos, pat, (fl & 0x80) ? BACKWARD : FORWARD, &start_pos,
                               &len, &ptr, &score)) {
      check_pos("search_for_fuzzy_match", pos);
    }
  }

  xfree(pat);
  xfree(text);
  return 0;
}
