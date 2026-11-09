// fzf_get_positions depends on what earlier calls left in the slab.
// gcc -fsanitize=address,undefined -I <dir of fzf.h> repro_v2_slab.c <fzf.c> -o r2 && ./r2
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fzf.h"
static void show(const char *what, fzf_position_t *p) {
  printf("%-28s", what);
  for (size_t i = 0; p && i < p->size; i++) printf(" %u", p->data[i]);
  printf("\n");
}
int main(void) {
  char q1[] = "__", q2[] = "c_c";
  fzf_pattern_t *a = fzf_parse_pattern(CaseSmart, false, q1, true);
  fzf_pattern_t *b = fzf_parse_pattern(CaseSmart, false, q2, true);
  fzf_slab_t *fresh = fzf_make_default_slab(), *used = fzf_make_default_slab();
  (void)fzf_get_score("cc_bb_b_   ", a, used);       // an earlier line, scored with the same slab
  fzf_position_t *p1 = fzf_get_positions("bcc_abc", b, fresh);
  fzf_position_t *p2 = fzf_get_positions("bcc_abc", b, used);
  show("fresh slab:", p1);
  show("after scoring another line:", p2);
  int same = p1->size == p2->size && !memcmp(p1->data, p2->data, p1->size * sizeof *p1->data);
  printf(same ? "same\n" : "DIFFERENT positions for the same text and pattern\n");
  fzf_free_positions(p1); fzf_free_positions(p2);
  fzf_free_pattern(a); fzf_free_pattern(b);
  fzf_free_slab(fresh); fzf_free_slab(used);
  return !same;
}
