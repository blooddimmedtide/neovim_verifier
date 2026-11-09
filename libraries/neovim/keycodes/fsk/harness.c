// Property: find_special_key never hands INT_MIN to simplify_key and never returns it
// (so special_to_buf in trans_special gets key != INT_MIN). Any source of LEN bytes.
#include "fsk.c"
char nondet_char(void); _Bool nondet_bool(void);
#ifndef LEN
#define LEN 10
#endif
int main(void) {
  char buf[LEN + 1];
  for (int i = 0; i < LEN; i++) buf[i] = nondet_char();
  buf[LEN] = 0;
  size_t n = vp_strlen(buf);
  const char *src = buf; int mods = 0; bool ds = false;
  int flags = nondet_int();
  int key = find_special_key(&src, n, &mods, flags, &ds);
  __CPROVER_assert(key != INT_MIN, "find_special_key result != INT_MIN");
  return 0;
}
