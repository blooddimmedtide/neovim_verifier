// CBMC harness: simplify_key / unsimplify_key (verbatim, from ../wp/build.py output kc.c)
// against a reference written from the doc comments: "the first table entry whose
// unshifted code is the key and whose modifier meets the modifiers; else unchanged".
#include "kc.c"
int nondet_int(void);

// Reference: entry j of the shifted-key table is (mask, shifted code, unshifted code).
static int ref_simplify(int key, int m, int *mo) {
  *mo = m;
  if ((m & (MOD_MASK_SHIFT | MOD_MASK_CTRL)) == 0) return key;
  if (key == TAB && (m & MOD_MASK_SHIFT)) { *mo = m & ~MOD_MASK_SHIFT; return K_S_TAB; }
  unsigned u = 0u - (unsigned)key;                 // the termcap bytes of a key code
  int b0 = (int)(u & 0xff), b1 = (int)((u >> 8) & 0xff);
  for (int j = 0; j < 75; j++) {
    const uint8_t *e = &modifier_keys_table[5 * j];
    if (e[3] == b0 && e[4] == b1 && (m & e[0])) { *mo = m & ~e[0]; return -(e[1] + 256 * e[2]); }
  }
  return key;
}
static int ref_unsimplify(int c, int m, int *mo) {
  *mo = m;
  if (c >= 0) return c;
  unsigned u = 0u - (unsigned)c;
  int b0 = (int)(u & 0xff), b1 = (int)((u >> 8) & 0xff);
  for (int j = 0; j < 75; j++) {
    const uint8_t *e = &modifier_keys_table[5 * j];
    if (e[1] == b0 && e[2] == b1) { *mo = m | e[0]; return -(e[3] + 256 * e[4]); }
  }
  return c;
}

int main(void) {
  // the table is what the C file says: 75 entries, then the terminator
  __CPROVER_assert(modifier_keys_table[375] == 0, "terminator");
  for (int j = 0; j < 75; j++) __CPROVER_assert(modifier_keys_table[5 * j] != 0, "entry mask");
  int key = nondet_int(), m = nondet_int(), want_m;
#ifndef ALLOW_INT_MIN
  __CPROVER_assume(key != INT_MIN);   // findings/keycodes-char-int-min.md
#endif
#ifdef UNSIMPLIFY
  int want = ref_unsimplify(key, m, &want_m);
  int got = unsimplify_key(key, &m);
#else
  int want = ref_simplify(key, m, &want_m);
  int got = simplify_key(key, &m);
#endif
  __CPROVER_assert(got == want, "key matches reference");
  __CPROVER_assert(m == want_m, "modifiers match reference");
  return 0;
}
