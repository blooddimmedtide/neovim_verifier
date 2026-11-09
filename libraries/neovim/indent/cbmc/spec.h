// Independent reference for the tab-stop layout used by 'tabstop' / 'vartabstop'.
// Written from the documented meaning (:help 'vartabstop'), not from indent.c:
// with widths w[1..n] (n >= 1) the tab stops are 0, S1=w1, S2=w1+w2, ..., Sn, and after Sn
// one stop every w[n] columns. Plain 'tabstop' ts is the layout n = 1, w1 = ts.
// All arithmetic in int64 so the reference itself cannot overflow.
#include <stdint.h>
typedef struct { int64_t prev, next, idx; } RefPos;  // prev: last stop <= c; next: first stop > c;
                                                     // idx: number of stops in (0, c]
static RefPos ref_pos(int64_t c, const int *w, int n)
{
  RefPos r;
  int64_t s = 0;
  for (int k = 1; k <= n; k++) {
    if (s + w[k] > c) { r.prev = s; r.next = s + w[k]; r.idx = k - 1; return r; }
    s += w[k];
  }
  int64_t q = (c - s) / w[n];
  r.prev = s + q * w[n]; r.next = r.prev + w[n]; r.idx = n + q;
  return r;
}
