// telescope-fzf-native: suffix pattern longer than the text reads before the text.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fzf.h"
int main(int argc, char **argv) {
  const char *pat_in = argc > 1 ? argv[1] : "abc$";
  const char *text_in = argc > 2 ? argv[2] : "x";
  char *pat = strdup(pat_in), *text = strdup(text_in);
  fzf_slab_t *slab = fzf_make_default_slab();
  fzf_pattern_t *p = fzf_parse_pattern(CaseSmart, false, pat, true);
  printf("score(%s, %s) = %d\n", text, pat_in, fzf_get_score(text, p, slab));
  fzf_free_pattern(p); fzf_free_slab(slab); free(pat); free(text);
  return 0;
}
