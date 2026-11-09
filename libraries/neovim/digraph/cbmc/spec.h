// Independent reference for digraph lookup, written from the documentation of
// getexactdigraph()/digraph_get() and :help digraph-table / digraph_get():
//  - special keys (negative codes) are never part of a digraph: the second char is returned;
//  - a user-defined digraph for the exact pair wins over the built-in table; a user entry
//    whose result is 0 means "deleted" and falls back to the built-in table;
//  - when nothing matches: <Space>{char} with meta_char gives {char}|0x80, else {char};
//  - digraph_get also tries the reversed pair {char2}{char1}.
// The reference looks up by "first index with matching pair" (a separate formulation).
static int ref_first(const digr_T *t, int n, int c1, int c2) {
  for (int k = 0; k < n; k++)
    if (t[k].char1 == c1 && t[k].char2 == c2) return k;
  return -1;
}
static int ref_exact(const digr_T *u, int nu, const digr_T *d, int nd, int c1, int c2, int meta) {
  if (c1 < 0 || c2 < 0) return c2;
  int k = ref_first(u, nu, c1, c2);
  int r = k >= 0 ? u[k].result : 0;
  if (r == 0) { k = ref_first(d, nd, c1, c2); r = k >= 0 ? d[k].result : 0; }
  if (r != 0) return r;
  return (c1 == ' ' && meta) ? (c2 | 0x80) : c2;
}
