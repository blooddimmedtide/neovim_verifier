// A line that satisfies the pattern only through an inverse term inside an OR
// group ("!a | b", "!a | !b") gets fzf_get_score() == 0, which the Telescope
// sorter (lua/telescope/_extensions/fzf.lua: score == 0 -> -1) treats as
// "filtered", so the line is hidden although fzf_get_positions() says it matches.
// gcc -fsanitize=address,undefined -I <dir of fzf.h> repro_inverse_or.c <fzf.c> && ./a.out
#include <stdio.h>
#include "fzf.h"
int main(void) {
  const char *pats[] = {"!a | b", "!a | !b"};
  int bad = 0;
  for (int i = 0; i < 2; i++) {
    char q[16];
    snprintf(q, sizeof q, "%s", pats[i]);
    fzf_pattern_t *p = fzf_parse_pattern(CaseSmart, false, q, true);
    fzf_slab_t *slab = fzf_make_default_slab();
    const char *line = "c";   // contains neither a nor b: "!a" holds
    int32_t s = fzf_get_score(line, p, slab);
    fzf_position_t *pos = fzf_get_positions(line, p, slab);
    printf("pattern %-8s line \"%s\": score %d, positions %s\n", pats[i], line, s,
           pos ? "returned (it matches)" : "NULL");
    if (s == 0 && pos) bad = 1;
    fzf_free_positions(pos);
    fzf_free_pattern(p);
    fzf_free_slab(slab);
  }
  return bad;
}
