// CBMC harnesses for the register.c helpers with pointer arithmetic over y_regs.
// ro.c is the verbatim, sha-pinned build of ../wp/build.py (ACSL there is only comments).
// The references below are written from the doc comments, not from the code.
#include "ro.c"
int nondet_int(void);
size_t nondet_size(void);
bool nondet_bool(void);

static String lines[NUM_REGISTERS];   // one line per register is all reg_empty can read

static void havoc_regs(yankreg_T *regs, int n)
{
  for (int k = 0; k < n; k++) {
    lines[k].size = nondet_size();
    lines[k].data = NULL;
    regs[k].y_array = nondet_bool() ? NULL : &lines[k];
    regs[k].y_size = nondet_size();
    __CPROVER_assume(regs[k].y_size <= 3);        // reg_empty only distinguishes 0, 1, more
    if (regs[k].y_size > 1 && regs[k].y_array) regs[k].y_array = &lines[k];  // never indexed past 0
    regs[k].y_type = (MotionType)(nondet_int() % 3);
    regs[k].y_width = nondet_int();
    regs[k].timestamp = (Timestamp)nondet_size();
    regs[k].additional_data = NULL;
  }
}

// Reference: a register holds no text when it has no lines or one empty charwise line.
static bool ref_empty(const yankreg_T *r)
{
  if (r->y_array == NULL || r->y_size == 0) return true;
  return r->y_size == 1 && r->y_type == kMTCharWise && r->y_array[0].size == 0;
}
// Reference register names (:help registers): 0-9, a-z, then '-'.
static char ref_name(int k) { return k < 10 ? (char)('0' + k) : k < 36 ? (char)('a' + k - 10) : '-'; }

void harness_get_unname_register(void)
{
  int k = nondet_int();
  __CPROVER_assume(-1 <= k && k < NUM_REGISTERS);
  y_previous = k == -1 ? NULL : &y_regs[k];
  int r = get_unname_register();
  assert(r == k);
}

// One call of op_reg_iter, starting from NULL or from any register pointer it can return.
void harness_op_reg_iter(void)
{
  havoc_regs(y_regs, NUM_REGISTERS);
  int start = nondet_int();
  __CPROVER_assume(-1 <= start && start < NUM_SAVED_REGISTERS);
  const void *iter = start == -1 ? NULL : (const void *)&y_regs[start];
  int prev = nondet_int();
  __CPROVER_assume(-1 <= prev && prev < NUM_REGISTERS);
  y_previous = prev == -1 ? NULL : &y_regs[prev];
  char name = 'Q'; yankreg_T reg; bool un = nondet_bool(); bool un0 = un;
#ifdef GLOBAL_ITER
  const void *next = op_global_reg_iter(iter, &name, &reg, &un);
#else
  const void *next = op_reg_iter(iter, y_regs, &name, &reg, &un);
#endif
  int from = start == -1 ? 0 : start;
  bool emp[NUM_SAVED_REGISTERS];
  for (int k = 0; k < NUM_SAVED_REGISTERS; k++) emp[k] = ref_empty(&y_regs[k]);
  int j = NUM_SAVED_REGISTERS;   // first non-empty register at or after `from`
  for (int k = NUM_SAVED_REGISTERS - 1; k >= 0; k--) if (k >= from && !emp[k]) j = k;
  if (j == NUM_SAVED_REGISTERS) {
    assert(name == NUL && next == NULL && un == un0);
    return;
  }
  assert(name == ref_name(j));
  assert(reg.y_array == y_regs[j].y_array && reg.y_size == y_regs[j].y_size
         && reg.y_type == y_regs[j].y_type && reg.y_width == y_regs[j].y_width
         && reg.timestamp == y_regs[j].timestamp && reg.additional_data == y_regs[j].additional_data);
  assert(un == (prev == j));
  int n = NUM_SAVED_REGISTERS;   // first non-empty register after j
  for (int k = NUM_SAVED_REGISTERS - 1; k >= 0; k--) if (k > j && !emp[k]) n = k;
  assert(next == (n == NUM_SAVED_REGISTERS ? NULL : (const void *)&y_regs[n]));
}
