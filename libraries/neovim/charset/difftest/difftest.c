// Differential test: charset.c's string helpers (exact upstream code from wp/build.py),
// compiled by gcc, against naive references written from the claim card (not from
// Neovim's code). Random short strings over an alphabet full of the bytes that matter
// (NUL, space, TAB, CR, LF, digits, hex letters, backslash, Ctrl-V, bytes > 127), plus
// every int value for hex2nr/nr2hex-style helpers. Usage: ./difftest <iterations> <seed>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
void *xmalloc(size_t n) { void *p = malloc(n ? n : 1); if (!p) abort(); return p; }
char *xstrchrnul(const char *str, char c) { while (*str && *str != c) str++; return (char *)str; }
#include CS_C

static unsigned long long s;
static unsigned rnd(void) { s ^= s << 13; s ^= s >> 7; s ^= s << 17; return (unsigned)(s >> 11); }
static const char AL[] = {0, ' ', '\t', '\r', '\n', '0', '1', '7', '9', 'a', 'f', 'g', 'A', 'F', 'G',
                          '\\', 22, '*', 'x', (char)0xe9, (char)0x80, (char)0xff};
static char pick(void) { return AL[rnd() % sizeof AL]; }
static unsigned long fails, checks;
#define CHECK(cond, what) do { checks++; if (!(cond)) { if (fails++ < 20) printf("MISMATCH %s (iter %lu)\n", what, it); } } while (0)

static int r_white(int c) { return c == 32 || c == 9; }
static int r_digit(int c) { return c >= 48 && c <= 57; }
static int r_bdigit(int c) { return c == 48 || c == 49; }
static int r_xdigit(int c) { return r_digit(c) || (c >= 65 && c <= 70) || (c >= 97 && c <= 102); }
static int r_hexval(int c) { const char *d = "0123456789abcdef", *D = "0123456789ABCDEF";
  for (int i = 0; i < 16; i++) if (c == d[i] || c == D[i]) return i; return -1; }
static size_t r_span(const char *p, int (*ok)(int)) { size_t i = 0; while (p[i] && ok(p[i])) i++; return i; }
static int nd(int c) { return !r_digit(c); }
static int nb(int c) { return !r_bdigit(c); }
static int nx(int c) { return !r_xdigit(c); }
static int nstop(int c) { return c != ' ' && c != '\t'; }
// skiptowhite_esc walk: an escape (backslash or Ctrl-V) with a non-NUL next byte takes two
static size_t r_esc(const char *p) {
  size_t i = 0;
  while (p[i] && p[i] != ' ' && p[i] != '\t') i += ((p[i] == '\\' || p[i] == 22) && p[i + 1]) ? 2 : 1;
  return i;
}
// backslash halving: "\x" -> "x" for any non-NUL x; a lone trailing backslash is kept
static void r_halve(const char *in, char *out) {
  size_t i = 0, j = 0;
  while (in[i]) { if (in[i] == '\\' && in[i + 1]) { out[j++] = in[i + 1]; i += 2; } else out[j++] = in[i++]; }
  out[j] = 0;
}

int main(int argc, char **argv) {
  unsigned long iters = argc > 1 ? strtoul(argv[1], 0, 0) : 1000000;
  s = argc > 2 ? strtoull(argv[2], 0, 0) : 0x9e3779b97f4a7c15ull;
  unsigned long it = 0;
  for (int c = -1000; c < 1000; c++) {   // small-int helpers over a wide range
    CHECK(!!ascii_iswhite(c) == r_white(c), "ascii_iswhite"); CHECK(!!ascii_isdigit(c) == r_digit(c), "ascii_isdigit");
    CHECK(!!ascii_isxdigit(c) == r_xdigit(c), "ascii_isxdigit"); CHECK(!!ascii_isbdigit(c) == r_bdigit(c), "ascii_isbdigit");
    if (r_xdigit(c)) CHECK(hex2nr(c) == r_hexval(c), "hex2nr");
  }
  for (unsigned n = 0; n < 4096; n++) CHECK((int)nr2hex(n) == "0123456789abcdef"[n % 16], "nr2hex");
  CHECK(nr2hex(UINT_MAX) == 'f', "nr2hex max");
  for (it = 0; it < iters; it++) {
    char a[24];
    for (size_t i = 0; i < sizeof a; i++) a[i] = pick();
    a[sizeof a - 1] = 0;
    size_t len = rnd() % 26;
    CHECK(skipwhite(a) == a + r_span(a, r_white), "skipwhite");
    { size_t k = 0; while (k < len && r_white(a[k])) k++; CHECK(skipwhite_len(a, len) == a + k, "skipwhite_len"); }
    CHECK(getwhitecols(a) == (intptr_t)r_span(a, r_white), "getwhitecols");
    CHECK(skipdigits(a) == a + r_span(a, r_digit), "skipdigits");
    CHECK(skipbin(a) == a + r_span(a, r_bdigit), "skipbin");
    CHECK(skiphex(a) == a + r_span(a, r_xdigit), "skiphex");
    CHECK(skiptodigit(a) == a + r_span(a, nd), "skiptodigit");
    CHECK(skiptobin(a) == a + r_span(a, nb), "skiptobin");
    CHECK(skiptohex(a) == a + r_span(a, nx), "skiptohex");
    CHECK(skiptowhite(a) == a + r_span(a, nstop), "skiptowhite");
    CHECK(skiptowhite_esc(a) == a + r_esc(a), "skiptowhite_esc");
    { size_t k = 0; while (a[k] && a[k] != '\n') k++; CHECK(skip_to_newline(a) == a + k, "skip_to_newline"); }
    { char b = a[r_span(a, r_white)]; CHECK(vim_isblankline(a) == (b == 0 || b == '\r' || b == '\n'), "vim_isblankline"); }
    { int want = (r_xdigit(a[0]) && r_xdigit(a[1])) ? 16 * r_hexval(a[0]) + r_hexval(a[1]) : -1;
      CHECK(hexhex2nr(a) == want, "hexhex2nr"); }
    CHECK(rem_backslash(a) == (a[0] == '\\' && a[1] != 0), "rem_backslash");
    { char want[24], got[24]; r_halve(a, want); memcpy(got, a, sizeof a); backslash_halve(got);
      CHECK(!strcmp(got, want), "backslash_halve");
      char *h = backslash_halve_save(a); CHECK(!strcmp(h, want), "backslash_halve_save"); free(h); }
  }
  printf("%lu checks, %lu mismatches\n", checks, fails);
  return fails != 0;
}
