// CBMC harness for cmdhist.c ring-buffer index functions.
// The functions in extracted.c are copied verbatim from src/nvim/cmdhist.c (see PINS).
#include <stdbool.h>
#include <stdlib.h>
#include <limits.h>
#include <stdint.h>
#define FUNC_ATTR_CONST
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define NUL '\0'
typedef enum { HIST_DEFAULT = -2, HIST_INVALID = -1, HIST_CMD = 0, HIST_SEARCH, HIST_EXPR,
               HIST_INPUT, HIST_DEBUG } HistoryType;
#define HIST_COUNT 5
typedef struct { int hisnum; char *hisstr; size_t hisstrlen; } histentry_T;
#ifndef N
#define N 4
#endif
static histentry_T *history[HIST_COUNT];
static int hisidx[HIST_COUNT];
static int hisnum[HIST_COUNT];
static int hislen;
static int maptick, last_maptick;
static char S;  // a non-NULL string
// hist_free_entry/clear_hist_entry: free is not modelled; the entry becomes empty.
static void clear_hist_entry(histentry_T *p) { p->hisnum = 0; p->hisstr = NULL; p->hisstrlen = 0; }
static void hist_free_entry(histentry_T *p) { clear_hist_entry(p); }
int nondet_int(void); bool nondet_bool(void);
#ifdef FIXED
#include "fixed.c"
#else
#include "extracted.c"
#endif

// Ring-buffer invariant that the rest of cmdhist.c maintains (documented: hisidx is the
// newest entry; hisnum is a unique, increasing id; empty slots have hisstr == NULL and
// lie after the filled ones going backwards from hisidx).
static int filled;  // number of filled entries, newest at hisidx, going backwards
static int age_idx[N];  // age_idx[r] = slot of the entry r steps older than the newest
static void setup(int t)
{
  hislen = HL;  // one run per table size 0..N (see run.sh)
  for (int k = 0; k < HIST_COUNT; k++) { history[k] = NULL; hisidx[k] = -1; hisnum[k] = 0; }
  if (hislen == 0) { filled = 0; return; }
  history[t] = malloc((size_t)hislen * sizeof(histentry_T));  // exact size
  __CPROVER_assume(history[t] != NULL);  // xmalloc never returns NULL
  hisidx[t] = nondet_int(); __CPROVER_assume(hisidx[t] >= -1 && hisidx[t] < hislen);
  filled = nondet_int();
  __CPROVER_assume(hisidx[t] < 0 ? filled == 0 : (filled >= 1 && filled <= hislen));
  int top = nondet_int(); __CPROVER_assume(top >= filled && top <= 1000);
  hisnum[t] = top;
  int i = hisidx[t] < 0 ? 0 : hisidx[t], prev = top + 1;
  for (int r = 0; r < hislen; r++) {  // r = age, 0 = newest
    age_idx[r] = i;
    if (r < filled) {
      int d = nondet_int(); __CPROVER_assume(d >= 1 && d <= 3);
      history[t][i].hisnum = (r == 0) ? top : prev - d;
      __CPROVER_assume(history[t][i].hisnum >= 1);
      prev = history[t][i].hisnum;
      history[t][i].hisstr = &S;
    } else { history[t][i].hisnum = 0; history[t][i].hisstr = NULL; }
    if (--i < 0) i = hislen - 1;
  }
}
// Reference for calc_hist_idx, written from its doc comment.
static int ref_calc(int t, int num)
{
  if (hislen == 0 || t < 0 || t >= HIST_COUNT || hisidx[t] < 0 || num == 0) return -1;
  for (int r = 0; r < filled; r++) {
    int i = age_idx[r];
    if (num > 0 && history[t][i].hisnum == num) return i;
    if (num < 0 && r == -(long long)num - 1) return i;
  }
  return -1;
}
int main(void)
{
  int t = nondet_int();
  int tt = (t >= 0 && t < HIST_COUNT) ? t : 0;
  setup(tt);
#ifdef CHECK_CHAR
  // hist_char2type: documented mapping
  int c = nondet_int();
  HistoryType h = hist_char2type(c);
  assert(h == (c == ':' ? HIST_CMD : c == '=' ? HIST_EXPR : c == '@' ? HIST_INPUT
               : c == '>' ? HIST_DEBUG : (c == 0 || c == '/' || c == '?') ? HIST_SEARCH
               : HIST_INVALID));
#endif
#ifdef CHECK_IDX
  // get_history_idx: id of newest entry or -1
  int g = get_history_idx(t);
  assert(g == ((hislen == 0 || t != tt || hisidx[tt] < 0) ? -1 : hisnum[tt]));
#endif
  // calc_hist_idx
  int num = nondet_int();
  int r = calc_hist_idx(t, num);
  assert(r == ref_calc(t, num));
#ifdef CHECK_DEL
  // del_history_idx: removes that entry, keeps the others in order
  int before = filled;
  int ok = del_history_idx(t, num);
  assert(ok == (r >= 0));
  if (ok) {
    assert(hisidx[tt] >= -1 && hisidx[tt] < hislen);
    int cnt = 0;
    for (int k = 0; k < hislen; k++) cnt += history[tt][k].hisstr != NULL;
    assert(cnt == before - 1);
  }
#endif
  return 0;
}
