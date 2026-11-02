// Differential test: strings.c helpers (exact upstream code from wp/build.py), compiled by
// gcc, against naive references written from the claim card. Random short strings over
// an alphabet of the bytes that matter. Usage: ./difftest <iterations> <seed>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
void *xmalloc(size_t n) { void *p = malloc(n ? n : 1); if (!p) abort(); return p; }
void *xmallocz(size_t n) { char *p = xmalloc(n + 1); p[n] = 0; return p; }
#include ST_C

static unsigned long long s;
static unsigned rnd(void) { s ^= s << 13; s ^= s >> 7; s ^= s << 17; return (unsigned)(s >> 11); }
static const char AL[] = {0, ' ', '\t', 'a', 'z', 'A', 'Z', 'm', 'M', '@', '[', '`', '{', '\\', 22,
                          (char)0xe9, (char)0x80, (char)0xff, (char)0xc9};
static char pick(void) { return AL[rnd() % sizeof AL]; }
static unsigned long fails, checks;
#define CHECK(cond, what) do { checks++; if (!(cond)) { if (fails++ < 20) printf("MISMATCH %s (iter %lu)\n", what, it); } } while (0)
static char r_up(char c) { return (c >= 'a' && c <= 'z') ? (char)(c - 32) : c; }
static int r_low(int c) { return (c >= 'A' && c <= 'Z') ? c + 32 : c; }

int main(int argc, char **argv) {
  unsigned long iters = argc > 1 ? strtoul(argv[1], 0, 0) : 1000000, it;
  s = argc > 2 ? strtoull(argv[2], 0, 0) : 0x9e3779b97f4a7c15ull;
  for (it = 0; it < iters; it++) {
    char a[24], b[24], w[40], x[40];
    for (size_t i = 0; i < sizeof a; i++) { a[i] = pick(); b[i] = (rnd() & 1) ? a[i] : pick(); }
    if (rnd() & 1) for (size_t i = 0; i < sizeof a; i++) b[i] = (rnd() & 3) ? (char)r_low(a[i]) : b[i];
    a[sizeof a - 1] = 0; b[sizeof b - 1] = 0;
    size_t n = strlen(a), len = rnd() % 26;
    size_t k = 0; while (k < len && a[k]) k++;
    // xstrnsave
    { char *r = xstrnsave(a, len); int ok = r[len] == 0;
      for (size_t i = 0; i < len; i++) ok &= r[i] == (i < k ? a[i] : 0);
      CHECK(ok, "xstrnsave"); free(r); }
    // vim_strup / vim_strcpy_up / vim_strsave_up
    { memcpy(w, a, sizeof a); vim_strup(w); int ok = 1; for (size_t i = 0; i <= n; i++) ok &= w[i] == r_up(a[i]);
      CHECK(ok, "vim_strup");
      memset(x, 7, sizeof x); vim_strcpy_up(x, a); ok = 1; for (size_t i = 0; i <= n; i++) ok &= x[i] == r_up(a[i]);
      CHECK(ok && x[n + 1] == 7, "vim_strcpy_up");
      char *r = vim_strsave_up(a); ok = 1; for (size_t i = 0; i <= n; i++) ok &= r[i] == r_up(a[i]);
      CHECK(ok, "vim_strsave_up"); free(r); }
    // vim_strncpy_up / vim_strnsave_up / vim_memcpy_up
    { memset(x, 7, sizeof x); vim_strncpy_up(x, a, len); int ok = x[k] == 0 && x[k + 1] == 7;
      for (size_t i = 0; i < k; i++) ok &= x[i] == r_up(a[i]);
      CHECK(ok, "vim_strncpy_up");
      char *r = vim_strnsave_up(a, len); ok = r[k] == 0; for (size_t i = 0; i < k; i++) ok &= r[i] == r_up(a[i]);
      CHECK(ok, "vim_strnsave_up"); free(r);
      size_t m = rnd() % sizeof a; memset(x, 7, sizeof x); vim_memcpy_up(x, a, m); ok = x[m] == 7;
      for (size_t i = 0; i < m; i++) ok &= x[i] == r_up(a[i]);
      CHECK(ok, "vim_memcpy_up"); }
    // del_trailing_spaces (called on a string inside a larger buffer, as Neovim does)
    { w[0] = 'x'; memcpy(w + 1, a, sizeof a); char *p = w + 1; size_t t = n;
      while (t > 1 && (p[t - 1] == ' ' || p[t - 1] == '\t') && p[t - 2] != '\\' && p[t - 2] != 22) t--;
      char want[24]; memcpy(want, a, sizeof a); for (size_t i = t; i < n; i++) want[i] = 0;
      del_trailing_spaces(p); CHECK(!memcmp(p, want, sizeof a), "del_trailing_spaces"); }
    // vim_strnicmp_asc
    { int want = 0; for (size_t i = 0; i < len; i++) { int d = r_low(a[i]) - r_low(b[i]); if (d) { want = d; break; } if (!a[i]) break; }
      CHECK(vim_strnicmp_asc(a, b, len) == want, "vim_strnicmp_asc"); }
    // has_non_ascii / has_non_ascii_len
    { int want = 0; for (size_t i = 0; i < n; i++) want |= (unsigned char)a[i] >= 128;
      CHECK(has_non_ascii(a) == want && !has_non_ascii(NULL), "has_non_ascii");
      want = 0; for (size_t i = 0; i < len && i < sizeof a; i++) want |= (unsigned char)a[i] >= 128;
      CHECK(has_non_ascii_len(a, len < sizeof a ? len : sizeof a) == want && !has_non_ascii_len(NULL, 5), "has_non_ascii_len"); }
    // concat_str
    { char *r = concat_str(a, b); size_t nb = strlen(b);
      CHECK(!memcmp(r, a, n) && !memcmp(r + n, b, nb + 1), "concat_str"); free(r); }
  }
  printf("%lu checks, %lu mismatches\n", checks, fails);
  return fails != 0;
}
