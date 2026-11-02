// Differential test: charset.c's string helpers (exact upstream code from wp/build.py),
// compiled by gcc, against naive references written from the claim card (not from
// Neovim's code). Random short strings over an alphabet full of the bytes that matter
// (NUL, space, TAB, CR, LF, digits, hex letters, backslash, Ctrl-V, bytes > 127), plus
// every int value for hex2nr/nr2hex-style helpers. Usage: ./difftest <iterations> <seed>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <stdbool.h>
#include <stdint.h>
#include <inttypes.h>
#include <errno.h>
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


// ---- vim_str2nr reference, from the claim card's description of the number syntax ----
static int r_av(int ml, long i) { return ml == 0 ? i < 2147483647L : i < ml; }
static int r_isdig(int b, int c) {
  return b == 2 ? (c == '0' || c == '1') : b == 8 ? (c >= '0' && c <= '7') : b == 10 ? r_digit(c) : r_xdigit(c);
}
static int r_alnum(int c) { return r_digit(c) || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'); }
static int r_pfx(const char *s, int ml, int a, char c1, char c2, int b) {
  return r_av(ml, a + 2) && s[a] == '0' && (s[a + 1] == c1 || s[a + 1] == c2) && r_isdig(b, s[a + 2]);
}
typedef struct { int pre, len; long long n; unsigned long long un; int ovf, fail; } R2N;
static R2N r_str2nr(const char *s, int what, int ml, int strict, int want_n, int ovf0) {
  R2N r = {0, 0, 0, 0, ovf0, 0};
  int a = s[0] == '-', base = 10, skip = 0, pre = 0;
  if (what & 128) {
    int k = what & ~(128 | 16);
    if (k == 4) { base = 16; skip = r_pfx(s, ml, a, 'x', 'X', 16) ? 2 : 0; }
    else if (k == 1) { base = 2; skip = r_pfx(s, ml, a, 'b', 'B', 2) ? 2 : 0; }
    else if (k == 0) { base = 10; }
    else { base = 8; skip = r_pfx(s, ml, a, 'o', 'O', 8) ? 2 : 0; }
  } else if ((what & 15) && r_av(ml, a + 1) && s[a] == '0' && s[a + 1] != '8' && s[a + 1] != '9') {
    if ((what & 4) && r_pfx(s, ml, a, 'x', 'X', 16)) { base = 16; skip = 2; pre = (unsigned char)s[a + 1]; }
    else if ((what & 1) && r_pfx(s, ml, a, 'b', 'B', 2)) { base = 2; skip = 2; pre = (unsigned char)s[a + 1]; }
    else if ((what & 8) && r_pfx(s, ml, a, 'o', 'O', 8)) { base = 8; skip = 2; pre = (unsigned char)s[a + 1]; }
    else if ((what & 2) && s[a + 1] >= '0' && s[a + 1] <= '7') {
      int ok = 1;
      for (long k = a + 2; r_av(ml, k) && r_digit(s[k]); k++) if (s[k] > '7') { ok = 0; break; }
      if (ok) { base = 8; pre = '0'; }
    }
  }
  long p = a + skip, p0 = p;
  unsigned __int128 v = 0; int big = 0;
  for (;;) {
    if ((what & 16) && p > p0 && r_av(ml, p) && s[p] == '\'' && r_av(ml, p + 1) && r_isdig(base, s[p + 1])) p++;
    if (!(r_av(ml, p) && r_isdig(base, s[p]))) break;
    if (!big) { v = v * base + (unsigned)r_hexval(s[p]); if (v > 0xFFFFFFFFFFFFFFFFull) big = 1; }
    p++;
  }
  unsigned long long un = big ? 0xFFFFFFFFFFFFFFFFull : (unsigned long long)v;
  if (big) r.ovf = 1;
  if (strict && p != ml && r_alnum(s[p])) { r.len = 0; r.fail = 1; return r; }
  r.pre = pre; r.len = (int)p;
  if (want_n) {
    if (un > 9223372036854775807ull) { r.ovf = 1; r.n = a ? INT64_MIN : INT64_MAX; if (!a) un = 9223372036854775807ull; }
    else r.n = a ? -(long long)un : (long long)un;
  }
  r.un = un;
  return r;
}
static const char AL2[] = {'-', '0', '0', '1', '7', '8', '9', 'x', 'X', 'b', 'B', 'o', 'O', 'a', 'f', 'g',
                           '\'', 0, ' ', 'z', 'F'};
static const int WHATS[] = {0, 1, 2, 4, 8, 15, 6, 10, 128, 129, 130, 132, 136, 138, 144, 145, 146, 148, 154, 16, 31, 18, 20};

// ---- getdigits reference: C-locale spaces, sign, decimal digits, saturating ----
static int r_getd(const char *s, size_t *end, __int128 *val) {   // returns 1 if digits present
  size_t w = 0; while (s[w] == ' ' || (s[w] >= 9 && s[w] <= 13)) w++;
  size_t d = w + (s[w] == '+' || s[w] == '-'), e = d; __int128 v = 0;
  while (s[e] >= '0' && s[e] <= '9') { if (v < ((__int128)1 << 100)) v = v * 10 + (s[e] - '0'); e++; }
  if (e == d) { *end = 0; *val = 0; return 0; }
  *end = e; *val = s[w] == '-' ? -v : v; return 1;
}
static const char AL3[] = {' ', '\t', '\n', '+', '-', '0', '1', '5', '9', '9', '9', 'a', 0};

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

  for (it = 0; it < iters; it++) {   // vim_str2nr
    char a[48];
    size_t L = rnd() % 40;
    for (size_t i = 0; i < sizeof a; i++) a[i] = (i < L) ? AL2[rnd() % sizeof AL2] : 0;
    if (rnd() % 4 == 0) for (size_t i = 1 + rnd() % 3; i < L; i++) a[i] = "0123456789abcdef"[rnd() % ((rnd() & 1) ? 10 : 16)];
    int what = WHATS[rnd() % (sizeof WHATS / sizeof WHATS[0])];
    int ml = (rnd() & 1) ? 0 : 1 + (int)(rnd() % 40);
    if (ml) for (int i = ml; i < (int)sizeof a; i++) a[i] = (char)(rnd() & 0xff);   // bytes past maxlen must not matter
    a[sizeof a - 1] = 0;
    int strict = rnd() & 1, wn = rnd() & 1, wu = rnd() & 1;
    bool ov = rnd() & 1; int ov0 = ov;
    int pre = -7, len = -7; varnumber_T n = -7; uvarnumber_T un = 7;
    R2N want = r_str2nr(a, what, ml, strict, wn, ov0);
    vim_str2nr(a, &pre, &len, what, wn ? &n : NULL, wu ? &un : NULL, ml, strict, &ov);
    CHECK(len == want.len, "vim_str2nr len");
    CHECK(ov == want.ovf, "vim_str2nr overflow");
    if (!want.fail) {
      CHECK(pre == want.pre, "vim_str2nr prep");
      if (wn) CHECK(n == want.n, "vim_str2nr nptr");
      if (wu) CHECK(un == want.un, "vim_str2nr unptr");
    } else {
      CHECK(pre == -7 && (!wn || n == -7) && (!wu || un == 7), "vim_str2nr strict leaves outputs");
    }
  }

  for (it = 0; it < iters; it++) {   // try_getdigits / getdigits*
    char a[40]; size_t L = rnd() % 36;
    for (size_t i = 0; i < sizeof a; i++) a[i] = (i < L) ? AL3[rnd() % sizeof AL3] : 0;
    if (rnd() & 1) for (size_t i = rnd() % 3 + 1; i < L; i++) a[i] = '0' + rnd() % 10;
    size_t e; __int128 v; int has = r_getd(a, &e, &v);
    char *p = a; intmax_t nr = 7;
    bool ok = try_getdigits(&p, &nr);
    int inr = v >= INTMAX_MIN && v <= INTMAX_MAX;
    CHECK(p == a + e && ok == (!has || inr) && nr == (!has ? 0 : v > INTMAX_MAX ? INTMAX_MAX : v < INTMAX_MIN ? INTMAX_MIN : (intmax_t)v), "try_getdigits");
    intmax_t def = (intmax_t)rnd() - 99;
    p = a; CHECK(getdigits(&p, false, def) == (!has ? 0 : inr ? (intmax_t)v : def) && p == a + e, "getdigits");
    int iin = v >= INT_MIN && v <= INT_MAX;
    p = a; CHECK(getdigits_int(&p, false, (int)def) == (!has ? 0 : iin ? (int)v : (int)def) && p == a + e, "getdigits_int");
    p = a; CHECK(getdigits_int32(&p, false, (int32_t)def) == (!has ? 0 : iin ? (int32_t)v : (int32_t)def), "getdigits_int32");
    p = a; CHECK(getdigits_long(&p, false, (long)def) == (!has ? 0 : inr ? (long)v : (long)def), "getdigits_long");
    if (!has || iin) { p = a; CHECK(getdigits_int(&p, true, 5) == (!has ? 0 : (int)v), "getdigits_int strict"); }
  }
  printf("%lu checks, %lu mismatches\n", checks, fails);
  return fails != 0;
}
