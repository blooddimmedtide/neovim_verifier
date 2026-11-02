// libFuzzer harness for telescope-fzf-native: first byte picks case mode,
// normalize and slab size; the rest is pattern and text split at the first 0x01.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "fzf.h"

int LLVMFuzzerTestOneInput(const uint8_t *d, size_t n) {
  if (n < 2) return 0;
  int mode = d[0] % 3;
  bool norm = d[0] & 4;
  bool small = d[0] & 8;
  d++; n--;
  const uint8_t *sep = memchr(d, 1, n);
  size_t pl = sep ? (size_t)(sep - d) : n;
  char *pat = malloc(pl + 1);
  memcpy(pat, d, pl);
  pat[pl] = 0;
  size_t tl = sep ? n - pl - 1 : 0;
  char *txt = malloc(tl + 1);
  if (tl) memcpy(txt, sep + 1, tl);
  txt[tl] = 0;
  for (size_t i = 0; i < pl; i++) if (!pat[i]) pat[i] = 'a';
  for (size_t i = 0; i < tl; i++) if (!txt[i]) txt[i] = 'a';
  fzf_slab_t *slab = small ? fzf_make_slab((fzf_slab_config_t){4, 4}) : fzf_make_default_slab();
  fzf_pattern_t *p = fzf_parse_pattern((fzf_case_types)mode, norm, pat, true);
  (void)fzf_get_score(txt, p, slab);
  fzf_position_t *pos = fzf_get_positions(txt, p, slab);
  fzf_free_positions(pos);
  fzf_free_pattern(p);
  fzf_free_slab(slab);
  free(pat);
  free(txt);
  return 0;
}
