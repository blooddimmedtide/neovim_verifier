#include "prelude.h"
#include GRID_C
#include "spec.h"
unsigned nondet_unsigned(void); int nondet_int(void); char nondet_char(void);
// Glyph cache model: n_keys exact-size bytes; the entry at idx is NUL terminated within
// MAX_SCHAR_SIZE bytes (assert(idx < n_keys) in the code + the cache's size invariant).
static void setup_cache(schar_T sc) {
  uint32_t n = nondet_unsigned();
  __CPROVER_assume(n >= 1 && n <= 40);
  glyph_cache.h.n_keys = n;
  glyph_cache.keys = malloc(n);
  if (ref_high(sc)) {
    uint32_t idx = ref_idx(sc);
    __CPROVER_assume(idx < n);
    uint32_t j = nondet_unsigned();
    __CPROVER_assume(j < MAX_SCHAR_SIZE && idx + j < n && glyph_cache.keys[idx + j] == 0);
  }
}
static schar_T any_sc(void) {
  schar_T sc = nondet_unsigned();
  // Non-high cells hold NUL-padded text: no NUL followed by a non-NUL byte.
  unsigned char b[4]; bytes_of(sc, b);
  if (b[0] != 0xFF) for (int i = 0; i < 3; i++) __CPROVER_assume(b[i] != 0 || b[i + 1] == 0);
  return sc;
}
void h_schar_high(void) { schar_T sc = nondet_unsigned(); assert(schar_high(sc) == ref_high(sc)); }
void h_schar_get_ascii(void) {
  schar_T sc = nondet_unsigned(); unsigned char b[4]; bytes_of(sc, b);
  char want = (b[0] < 0x80 && b[1] == 0 && b[2] == 0 && b[3] == 0) ? (char)b[0] : NUL;
  assert(schar_get_ascii(sc) == want);
}
void h_schar_len(void) {
  schar_T sc = any_sc(); setup_cache(sc); size_t n; char tmp[5];
  ref_text(sc, &n, tmp); assert(schar_len(sc) == n);
}
void h_schar_get_adv(void) {
  schar_T sc = any_sc(); setup_cache(sc); size_t n; char tmp[5];
  const char *t = ref_text(sc, &n, tmp);
  char *buf = malloc(MAX_SCHAR_SIZE); char *p = buf;
  size_t r = schar_get_adv(&p, sc);
  assert(r == n && p == buf + n);
  for (size_t i = 0; i < n; i++) assert(buf[i] == t[i]);
}
void h_schar_get(void) {
  schar_T sc = any_sc(); setup_cache(sc); size_t n; char tmp[5];
  const char *t = ref_text(sc, &n, tmp);
  char *buf = malloc(MAX_SCHAR_SIZE);
  size_t r = schar_get(buf, sc);
  assert(r == n && n < MAX_SCHAR_SIZE && buf[n] == NUL);
  for (size_t i = 0; i < n; i++) assert(buf[i] == t[i]);
}
void h_schar_get_first_byte(void) {
  schar_T sc = any_sc(); setup_cache(sc); size_t n; char tmp[5];
  const char *t = ref_text(sc, &n, tmp);
  assert(schar_get_first_byte(sc) == t[0]);
}
void h_schar_in_arabic_block(void) {
  schar_T sc = any_sc(); setup_cache(sc); size_t n; char tmp[5];
  unsigned char f = (unsigned char)ref_text(sc, &n, tmp)[0];
  assert(schar_in_arabic_block(sc) == (f == 0xD8 || f == 0xD9));  // U+0600..U+07FF lead bytes
}
void h_schar_from_char(void) {
  int c = nondet_int(); __CPROVER_assume(c >= 0);   // documented: "a unicode character"
  unsigned char want[4] = { 0 };
  ref_utf8(c < 0x200000 ? c : 0xFFFD, want);
  schar_T sc = schar_from_char(c); unsigned char b[4]; bytes_of(sc, b);
  for (int i = 0; i < 4; i++) assert(b[i] == want[i]);
}
void h_grid_adjust(void) {
  GridView v; ScreenGrid g; v.target = &g; v.row_offset = nondet_int(); v.col_offset = nondet_int();
  int r = nondet_int(), c = nondet_int(); int r0 = r, c0 = c;
#ifndef NO_OFFSET_PRE
  // Caller precondition (NOT documented): screen positions fit in int.
  __CPROVER_assume((long)r + v.row_offset >= INT_MIN && (long)r + v.row_offset <= INT_MAX);
  __CPROVER_assume((long)c + v.col_offset >= INT_MIN && (long)c + v.col_offset <= INT_MAX);
#endif
  ScreenGrid *res = grid_adjust(&v, &r, &c);
  assert(res == &g && (long)r == (long)r0 + v.row_offset && (long)c == (long)c0 + v.col_offset);
}
