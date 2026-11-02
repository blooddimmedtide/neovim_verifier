// fzf_get_score returns a negative score for a matching line when the line is
// long enough that v2 falls back to v1 (text length * pattern length > 102400
// with the default slab). Telescope's sorter turns score s into 1/s and treats
// smaller as better, so such a line is ranked above every real match.
// gcc -fsanitize=address,undefined -I <dir of fzf.h> repro_negative_score.c <fzf.c> && ./a.out
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fzf.h"
int main(void) {
  size_t n = 60000;
  char *line = malloc(n + 1);
  memset(line, 'x', n);
  line[0] = 'a';
  line[61] = 'b';   // "a" + 60 x + "b" + more x
  line[n] = 0;
  char q[] = "ab";
  fzf_pattern_t *p = fzf_parse_pattern(CaseSmart, false, q, true);
  fzf_slab_t *slab = fzf_make_default_slab();
  int32_t s = fzf_get_score(line, p, slab);
  fzf_position_t *pos = fzf_get_positions(line, p, slab);
  printf("score %d, positions %s\n", s, pos ? "returned (it matches)" : "NULL");
  fzf_free_positions(pos);
  fzf_free_pattern(p);
  fzf_free_slab(slab);
  free(line);
  return s > 0 ? 0 : 1;
}
