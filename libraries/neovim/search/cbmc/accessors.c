// CBMC proofs of full functional correctness of search.c's small accessors.
// Each harness starts from arbitrary values of every search.c global the
// extracted code has, calls one function with arbitrary arguments (within the
// stated precondition) and checks the result and that every global it should
// not touch is unchanged ("frame"). The specs come from the functions' names,
// doc comments and callers, not from their bodies.
#include <stdlib.h>
#include <limits.h>
#include SEARCH_C

int nondet_int(void);
char nondet_char(void);
bool nondet_bool(void);
size_t nondet_size(void);
int64_t nondet_i64(void);
uint64_t nondet_u64(void);
uint8_t nondet_u8(void);
char *nondet_ptr(void);
AdditionalData *nondet_ad(void);

static SearchPattern s_spats[2];
static int s_last_idx, s_lastc_bytelen;
static Direction s_lastcdir;
static bool s_last_t_cmd;
static char *s_mr_pattern;
static uint8_t s_lastc[2];
static char s_lastc_bytes[MAX_SCHAR_SIZE + 1];

static void havoc(void)
{
  for (int i = 0; i < 2; i++) {
    spats[i].pat = nondet_ptr();
    spats[i].patlen = nondet_size();
    spats[i].magic = nondet_bool();
    spats[i].no_scs = nondet_bool();
    spats[i].timestamp = nondet_u64();
    spats[i].off.dir = nondet_char();
    spats[i].off.line = nondet_bool();
    spats[i].off.end = nondet_bool();
    spats[i].off.off = nondet_i64();
    spats[i].additional_data = nondet_ad();
  }
  last_idx = nondet_int();
  lastcdir = (Direction)nondet_int();
  last_t_cmd = nondet_bool();
  mr_pattern = nondet_ptr();
  lastc[0] = nondet_u8();
  lastc[1] = nondet_u8();
  for (int i = 0; i <= MAX_SCHAR_SIZE; i++) {
    lastc_bytes[i] = nondet_char();
  }
  lastc_bytelen = nondet_int();
  // snapshot
  for (int i = 0; i < 2; i++) {
    s_spats[i] = spats[i];
  }
  s_last_idx = last_idx; s_lastcdir = lastcdir; s_last_t_cmd = last_t_cmd;
  s_mr_pattern = mr_pattern; s_lastc[0] = lastc[0]; s_lastc[1] = lastc[1];
  for (int i = 0; i <= MAX_SCHAR_SIZE; i++) {
    s_lastc_bytes[i] = lastc_bytes[i];
  }
  s_lastc_bytelen = lastc_bytelen;
}

static bool sp_same(int i, bool except_dir)
{
  SearchPattern a = spats[i], b = s_spats[i];
  return a.pat == b.pat && a.patlen == b.patlen && a.magic == b.magic && a.no_scs == b.no_scs
         && a.timestamp == b.timestamp && (except_dir || a.off.dir == b.off.dir)
         && a.off.line == b.off.line && a.off.end == b.off.end && a.off.off == b.off.off
         && a.additional_data == b.additional_data;
}

// Frame: which globals may change.
enum { F_SPATS0_DIR = 1, F_LAST_IDX = 2, F_LASTCDIR = 4, F_LAST_T_CMD = 8 };
static void frame(int may)
{
  __CPROVER_assert(sp_same(0, may & F_SPATS0_DIR) && sp_same(1, false), "frame: spats");
  __CPROVER_assert((may & F_LAST_IDX) || last_idx == s_last_idx, "frame: last_idx");
  __CPROVER_assert((may & F_LASTCDIR) || lastcdir == s_lastcdir, "frame: lastcdir");
  __CPROVER_assert((may & F_LAST_T_CMD) || last_t_cmd == s_last_t_cmd, "frame: last_t_cmd");
  __CPROVER_assert(mr_pattern == s_mr_pattern, "frame: mr_pattern");
  __CPROVER_assert(lastc[0] == s_lastc[0] && lastc[1] == s_lastc[1], "frame: lastc");
  __CPROVER_assert(lastc_bytelen == s_lastc_bytelen, "frame: lastc_bytelen");
  for (int i = 0; i <= MAX_SCHAR_SIZE; i++) {
    __CPROVER_assert(lastc_bytes[i] == s_lastc_bytes[i], "frame: lastc_bytes");
  }
}

// get_search_pat(): the pattern last compiled by search_regcomp().
void h_get_search_pat(void) { havoc(); char *r = get_search_pat(); __CPROVER_assert(r == s_mr_pattern, "result"); frame(0); }

// last_search_pattern() / _len(): the last search (not substitute) pattern and its length.
void h_last_search_pattern(void) { havoc(); char *r = last_search_pattern(); __CPROVER_assert(r == s_spats[RE_SEARCH].pat, "result"); frame(0); }
void h_last_search_pattern_len(void) { havoc(); size_t r = last_search_pattern_len(); __CPROVER_assert(r == s_spats[RE_SEARCH].patlen, "result"); frame(0); }

// last_csearch(): the stored character-search bytes (the buffer itself).
void h_last_csearch(void) { havoc(); const char *r = last_csearch(); __CPROVER_assert(r == lastc_bytes, "result"); frame(0); }

// last_csearch_forward(): 1 if the last f/t search went forward, else 0.
void h_last_csearch_forward(void) { havoc(); int r = last_csearch_forward(); __CPROVER_assert(r == (s_lastcdir == FORWARD ? 1 : 0), "result"); frame(0); }

// last_csearch_until(): 1 if the last character search was t/T, else 0.
void h_last_csearch_until(void) { havoc(); int r = last_csearch_until(); __CPROVER_assert(r == (s_last_t_cmd ? 1 : 0), "result"); frame(0); }

// set_csearch_direction(d): any Direction value is stored as given.
void h_set_csearch_direction(void)
{
  havoc();
  Direction d = (Direction)nondet_int();
  __CPROVER_assume(d == kDirectionNotSet || d == FORWARD || d == BACKWARD || d == FORWARD_FILE || d == BACKWARD_FILE);
  set_csearch_direction(d);
  __CPROVER_assert(lastcdir == d, "stored");
  __CPROVER_assert(last_csearch_forward() == (d == FORWARD), "read back");
  frame(F_LASTCDIR);
}

// set_csearch_until(t): stores whether t is non-zero (any int).
void h_set_csearch_until(void)
{
  havoc();
  int t = nondet_int();
  set_csearch_until(t);
  __CPROVER_assert(last_t_cmd == (t != 0), "stored");
  __CPROVER_assert(last_csearch_until() == (t != 0 ? 1 : 0), "read back");
  frame(F_LAST_T_CMD);
}

// set_search_direction(c): the search pattern's direction becomes c, for any
// c that fits in a char (the only caller passes '/' or '?').
void h_set_search_direction(void)
{
  havoc();
  int c = nondet_int();
  __CPROVER_assume(c >= CHAR_MIN && c <= CHAR_MAX);
  set_search_direction(c);
  __CPROVER_assert(spats[0].off.dir == c, "stored");
  frame(F_SPATS0_DIR);
}

// first_submatch(rp): the lowest sub-match number 1..9 that matched
// (startpos[i].lnum >= 0), or 0 when none did. Reads only startpos[1..9].
void h_first_submatch(void)
{
  havoc();
  regmmatch_T *rp = malloc(sizeof(regmmatch_T));
  int r = first_submatch(rp);
  int want = 0;
  for (int i = 9; i >= 1; i--) {
    if (rp->startpos[i].lnum >= 0) {
      want = i;
    }
  }
  __CPROVER_assert(r == want, "lowest matched sub-match, else 0");
  frame(0);
}

// search_pattern_cleared(sub): whether the substitute (sub) or search pattern is unset.
void h_search_pattern_cleared(void)
{
  havoc();
  bool sub = nondet_bool();
  bool r = search_pattern_cleared(sub);
  __CPROVER_assert(r == (s_spats[sub ? RE_SUBST : RE_SEARCH].pat == NULL), "result");
  frame(0);
}

// set_last_used_pattern(sub) then search_was_last_used(): the search pattern
// was last used exactly when sub is false.
void h_set_last_used_pattern(void)
{
  havoc();
  bool sub = nondet_bool();
  set_last_used_pattern(sub);
  __CPROVER_assert(last_idx == (sub ? RE_SUBST : RE_SEARCH), "stored");
  __CPROVER_assert(search_was_last_used() == !sub, "read back");
  frame(F_LAST_IDX);
}

void h_search_was_last_used(void) { havoc(); bool r = search_was_last_used(); __CPROVER_assert(r == (s_last_idx == RE_SEARCH), "result"); frame(0); }
