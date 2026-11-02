// The reference specification (../../cbmc/spec.h) behind fzf.c's interface, so
// the plugin's own test expectations can be checked against the spec:
// test.c is compiled with -Dfzf_<alg>=ref_<alg> for the five algorithms with a
// full reference (v2 has none and stays the real one).
#include <stdlib.h>
#include "spec.h"
#include "fzf.h"
typedef r_result (*reff)(const unsigned char *, size_t, const unsigned char *, size_t, bool, size_t *, size_t *);
static fzf_result_t run(reff ref, bool cs, fzf_string_t *t, fzf_string_t *p, fzf_position_t *pos) {
  size_t want[256], k;
  r_result r = ref((const unsigned char *)t->data, t->size, (const unsigned char *)p->data, p->size, cs, want, &k);
  if (pos)
    for (size_t i = 0; i < k; i++) {
      if (pos->size == pos->cap) { pos->cap = pos->cap ? 2 * pos->cap : 1; pos->data = realloc(pos->data, pos->cap * sizeof *pos->data); }
      pos->data[pos->size++] = (uint32_t)want[i];
    }
  return (fzf_result_t){r.start, r.end, r.score};
}
#define ADAPT(name, ref)                                                       \
  fzf_result_t name(bool cs, bool norm, fzf_string_t *t, fzf_string_t *p,      \
                    fzf_position_t *pos, fzf_slab_t *slab) {                   \
    (void)norm; (void)slab; return run(ref, cs, t, p, pos);                    \
  }
ADAPT(ref_fuzzy_match_v1, ref_v1)
ADAPT(ref_exact_match_naive, ref_exact)
ADAPT(ref_prefix_match, ref_prefix)
ADAPT(ref_suffix_match, ref_suffix)
ADAPT(ref_equal_match, ref_equal)
