// Differential test: compiled extracted code vs spec.h, exhaustive over all strings of
// length 0..5 on the alphabet below (covers every branch the spec distinguishes).
#include <stdio.h>
#define __CPROVER_assume(x) ((void)0)
#define __CPROVER_assert(x, m) ((void)0)
#define main harness_main
#include "harness.c"
#undef main
char nondet_char(void){return 0;} size_t nondet_size(void){return 1;} int nondet_int(void){return 0;}
static const char A[] = "<>t_nomvreyp=+^-";
int main(void){
  char s[8]; long bad = 0, cnt = 0; size_t K = sizeof A - 1;
  for (int len = 0; len <= 5; len++) {
    long tot = 1; for (int i = 0; i < len; i++) tot *= K;
    for (long c = 0; c < tot; c++) { long x = c;
      for (int i = 0; i < len; i++) { s[i] = A[x % K]; x /= K; } s[len] = 0;
      size_t n = len + 1, adv; char *p = s; cnt++;
      if (get_op(s) != ref_get_op(s, n)) bad++;
      set_prefix_T w = ref_prefix(s, n, &adv); if (get_option_prefix(&p) != w || p != s + adv) bad++;
      long r = ref_tty_end(s, n); const char *e = find_tty_option_end(s);
      if (r < 0 ? e != NULL : e != s + r) bad++; } }
  const char *ex[] = {"term","ttytype","termx","<t_Co>","<t_Co","t_Co","<foo>","<>","<",""};
  for (int i = 0; i < 10; i++) { long r = ref_tty_end(ex[i], strlen(ex[i]) + 1);
    if (r != (find_tty_option_end(ex[i]) ? find_tty_option_end(ex[i]) - ex[i] : -1)) bad++; }
  printf("%ld strings, %ld mismatches\n", cnt, bad); return bad != 0; }
