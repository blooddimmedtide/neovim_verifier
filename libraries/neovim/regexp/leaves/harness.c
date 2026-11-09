// CBMC proofs of full functional correctness of 8 small regexp.c functions.
// Specs come from regexp.c's comments, :help pattern and the callers, not
// from the bodies:
//  - "Magic characters have a special meaning ... Magic characters are
//    negative." A magic char is c - 256 for a byte c (0..255); plain chars
//    are >= 0.
//  - \r \t \e \b in a pattern mean CR (13), TAB (9), ESC (27), BS (8).
//  - \%23l, \%<23l, \%>23l: equal to, before (less than), after (greater
//    than) the number 23; the backtracking program stores the number as 4
//    big-endian bytes at offset 3 of the node and the comparison at offset 7.
#include <stdlib.h>
#include <stdint.h>
#include REGEXP_LEAVES_C

int nondet_int(void);
unsigned nondet_unsigned(void);
uint32_t nondet_u32(void);
uintmax_t nondet_umax(void);
bool nondet_bool(void);

#define SPEC_MAGIC(c) ((c) - 256)   // the encoding, from the comment above

// no_Magic: a magic char gives its plain byte; a plain char is unchanged.
void h_no_Magic(void)
{
  int c = nondet_int();
  if (nondet_bool()) {
    __CPROVER_assume(c >= 0 && c <= 255);
    __CPROVER_assert(no_Magic(SPEC_MAGIC(c)) == c, "magic -> plain");
  } else {
    __CPROVER_assume(c >= 0);
    __CPROVER_assert(no_Magic(c) == c, "plain unchanged");
  }
}

// toggle_Magic: magic <-> plain, for plain c >= 0 (any value) and magic chars.
void h_toggle_Magic(void)
{
  int c = nondet_int();
  if (nondet_bool()) {
    __CPROVER_assume(c >= 0 && c <= 255);
    __CPROVER_assert(toggle_Magic(SPEC_MAGIC(c)) == c, "magic -> plain");
  } else {
    __CPROVER_assume(c >= 0);
    __CPROVER_assert(toggle_Magic(c) == SPEC_MAGIC(c), "plain -> magic");
  }
}

// re_multi_type: magic @ = ? are "one" multis, magic * + { are "many"
// multis, anything else (any int) is not a multi.
void h_re_multi_type(void)
{
  int c = nondet_int();
  int r = re_multi_type(c);
  int want = (c == SPEC_MAGIC('@') || c == SPEC_MAGIC('=') || c == SPEC_MAGIC('?')) ? 1
             : (c == SPEC_MAGIC('*') || c == SPEC_MAGIC('+') || c == SPEC_MAGIC('{')) ? 2 : 0;
  __CPROVER_assert(r == want, "multi type");
  __CPROVER_assert(NOT_MULTI == 0 && MULTI_ONE == 1 && MULTI_MULT == 2, "constants");
}

// backslash_trans: r t e b -> CR TAB ESC BS, every other int unchanged.
void h_backslash_trans(void)
{
  int c = nondet_int();
  int r = backslash_trans(c);
  int want = c == 'r' ? 13 : c == 't' ? 9 : c == 'e' ? 27 : c == 'b' ? 8 : c;
  __CPROVER_assert(r == want, "translation");
}

// re_multiline: true exactly when the program's "can match a NL" flag (4) is set.
void h_re_multiline(void)
{
  regprog_T prog;
  prog.engine = NULL;
  prog.regflags = nondet_unsigned();
  prog.re_engine = nondet_unsigned();
  prog.re_flags = nondet_unsigned();
  prog.re_in_use = nondet_bool();
  regprog_T old = prog;
  int r = re_multiline(&prog);
  __CPROVER_assert((r != 0) == ((old.regflags & 4u) != 0), "NL flag");
  __CPROVER_assert(prog.regflags == old.regflags && prog.re_engine == old.re_engine
                   && prog.re_flags == old.re_flags && prog.re_in_use == old.re_in_use, "prog unchanged");
}

// vim_regcomp_had_eol: the value vim_regcomp() left in had_eol.
void h_vim_regcomp_had_eol(void)
{
  had_eol = nondet_int();
  int old = had_eol;
  __CPROVER_assert(vim_regcomp_had_eol() == old && had_eol == old, "had_eol");
}

// re_num_cmp(val, scan): compare position val with the node's number n
// (big-endian scan[3..6]) using scan[7]: '>' val > n, '<' val < n, else ==.
// scan points to exactly 8 readable bytes.
void h_re_num_cmp(void)
{
  uint32_t val = nondet_u32();
  uint8_t *scan = malloc(8);
  uint32_t n = ((uint32_t)scan[3] << 24) | ((uint32_t)scan[4] << 16) | ((uint32_t)scan[5] << 8) | scan[6];
  int r = re_num_cmp(val, scan);
  int want = scan[7] == '>' ? val > n : scan[7] == '<' ? val < n : val == n;
  __CPROVER_assert(r == want, "comparison");
}

// nfa_re_num_cmp(val, op, pos): op 1 (\%>) pos > val, op 2 (\%<) pos < val,
// anything else pos == val. Any values.
void h_nfa_re_num_cmp(void)
{
  uintmax_t val = nondet_umax(), pos = nondet_umax();
  int op = nondet_int();
  bool r = nfa_re_num_cmp(val, op, pos);
  bool want = op == 1 ? pos > val : op == 2 ? pos < val : pos == val;
  __CPROVER_assert(r == want, "comparison");
}
