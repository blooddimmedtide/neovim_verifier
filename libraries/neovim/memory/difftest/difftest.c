// Differential test: memory.c's 15 string functions, compiled by gcc (with glibc),
// against naive references written from the claim card (not from Neovim's code).
// Random short buffers over a small alphabet (NUL, the searched byte, bytes > 127)
// so matches, NULs and sign issues are frequent. Usage: ./difftest <iterations> <seed>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include MEM_C

static unsigned long long s;
static unsigned rnd(void) { s ^= s << 13; s ^= s >> 7; s ^= s << 17; return (unsigned)(s >> 11); }
static const char AL[] = {0, 'a', 'b', (char)0xe9, (char)0x80, (char)0xff, 'z'};
static char pick(void) { return AL[rnd() % sizeof AL]; }
static unsigned long fails, checks;
#define CHECK(cond, what) do { checks++; if (!(cond)) { if (fails++ < 20) printf("MISMATCH %s (iter %lu)\n", what, it); } } while (0)

static size_t r_strlen(const char *p) { size_t i = 0; while (p[i]) i++; return i; }

int main(int argc, char **argv) {
  unsigned long iters = argc > 1 ? strtoul(argv[1], 0, 0) : 1000000;
  s = argc > 2 ? strtoull(argv[2], 0, 0) : 0x9e3779b97f4a7c15ull;
  for (unsigned long it = 0; it < iters; it++) {
    size_t len = rnd() % 24;
    char a[32], b[32], d1[64], d2[64];
    for (size_t i = 0; i < sizeof a; i++) { a[i] = pick(); b[i] = (rnd() & 1) ? a[i] : pick(); }
    a[sizeof a - 1] = 0; b[sizeof b - 1] = 0;    // both are strings
    char c = pick(), x = pick(), cn = c ? c : 'a';
    // xmemcpyz
    memset(d1, 7, sizeof d1);
    CHECK(xmemcpyz(d1, a, len) == d1 && !memcmp(d1, a, len) && d1[len] == 0 && d1[len + 1] == 7, "xmemcpyz");
    // xstrnlen
    { size_t r = 0; while (r < len && a[r]) r++; CHECK(xstrnlen(a, len) == r, "xstrnlen"); }
    // xstrchrnul
    { const char *r = a; while (*r && *r != c) r++; CHECK(xstrchrnul(a, c) == r, "xstrchrnul"); }
    // xmemscan
    { size_t r = 0; while (r < len && a[r] != c) r++; CHECK((char *)xmemscan(a, c, len) == a + r, "xmemscan"); }
    // strchrsub (c != NUL)
    { memcpy(d1, a, 32); memcpy(d2, a, 32); size_t n = r_strlen(a);
      for (size_t i = 0; i <= n; i++) if (d2[i] == cn) d2[i] = x;
      strchrsub(d1, cn, x); CHECK(!memcmp(d1, d2, 32), "strchrsub"); }
    // memchrsub
    { memcpy(d1, a, 32); memcpy(d2, a, 32);
      for (size_t i = 0; i < len; i++) if (d2[i] == c) d2[i] = x;
      memchrsub(d1, c, x, len); CHECK(!memcmp(d1, d2, 32), "memchrsub"); }
    // strcnt (c != NUL), memcnt
    { size_t n = r_strlen(a), k = 0; for (size_t i = 0; i < n; i++) k += a[i] == cn; CHECK(strcnt(a, cn) == k, "strcnt"); }
    { size_t k = 0; for (size_t i = 0; i < len; i++) k += a[i] == c; CHECK(memcnt(a, c, len) == k, "memcnt"); }
    // xstpcpy
    { memset(d1, 7, sizeof d1); size_t n = r_strlen(a); char *r = xstpcpy(d1, a);
      CHECK(r == d1 + n && !memcmp(d1, a, n + 1) && d1[n + 1] == 7, "xstpcpy"); }
    // xstpncpy
    { memset(d1, 7, sizeof d1); size_t n = r_strlen(a), k = n < len ? n : len; char *r = xstpncpy(d1, a, len);
      int ok = r == d1 + k && !memcmp(d1, a, k) && d1[len] == 7;
      for (size_t i = k; i < len; i++) ok &= d1[i] == 0;
      CHECK(ok, "xstpncpy"); }
    // xstrlcpy
    { memset(d1, 7, sizeof d1); size_t n = r_strlen(a), ds = rnd() % 26; size_t r = xstrlcpy(d1, a, ds);
      int ok = r == n;
      if (ds) { size_t k = n < ds - 1 ? n : ds - 1; ok &= !memcmp(d1, a, k) && d1[k] == 0; for (size_t i = k + 1; i < 64; i++) ok &= d1[i] == 7; }
      else for (size_t i = 0; i < 64; i++) ok &= d1[i] == 7;
      CHECK(ok, "xstrlcpy"); }
    // xstrlcat
    { memset(d1, 7, sizeof d1); size_t m = rnd() % 10; memcpy(d1, b, m); for (size_t i = 0; i < m; i++) if (!d1[i]) d1[i] = 'q'; d1[m] = 0;
      memcpy(d2, d1, 64);
      size_t n = r_strlen(a), ds = m + 1 + rnd() % 24; size_t r = xstrlcat(d1, a, ds);
      size_t k = n < ds - m - 1 ? n : ds - m - 1;
      memcpy(d2 + m, a, k); d2[m + k] = 0;
      CHECK(r == m + n && !memcmp(d1, d2, 64), "xstrlcat"); }
    // xmemrchr
    { uint8_t uc = (uint8_t)c; const char *r = NULL; for (size_t i = 0; i < len; i++) if ((uint8_t)a[i] == uc) r = a + i;
      CHECK((const char *)xmemrchr(a, uc, len) == r, "xmemrchr"); }
    // strequal, strnequal (with NULL)
    { int na = rnd() % 8 == 0, nb = rnd() % 8 == 0; const char *pa = na ? NULL : a, *pb = nb ? NULL : b;
      int eq = (na && nb) || (!na && !nb && !strcmp(a, b));
      CHECK(strequal(pa, pb) == eq, "strequal");
      size_t n = rnd() % 34; int neq = (na && nb);
      if (!na && !nb) { neq = 1; for (size_t i = 0; i < n; i++) { if (a[i] != b[i]) { neq = 0; break; } if (!a[i]) break; } }
      CHECK(strnequal(pa, pb, n) == neq, "strnequal"); }
  }
  printf("%lu checks, %lu mismatches\n", checks, fails);
  return fails != 0;
}
