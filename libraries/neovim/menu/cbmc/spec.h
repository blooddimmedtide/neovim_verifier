/* Independent references, written from the documented meaning of each helper. */
#include <stddef.h>
#include <stdbool.h>
static size_t r_len(const char *s) { size_t n = 0; while (s[n]) n++; return n; }
/* s starts with the literal prefix w (w has k bytes, none NUL). */
static bool r_prefix(const char *s, const char *w, size_t k) {
  for (size_t i = 0; i < k; i++) { if (s[i] != w[i]) return false; } return true; }
/* The menu-name part of s: bytes before the first NUL or TAB. */
static size_t r_part(const char *s) { size_t n = 0; while (s[n] && s[n] != '\t') n++; return n; }
static bool r_samepart(const char *a, const char *b) {
  size_t la = r_part(a), lb = r_part(b);
  if (la != lb) return false;
  for (size_t i = 0; i < la; i++) if (a[i] != b[i]) return false;
  return true; }
/* End of one path element: stops at NUL, '.', space or tab; "\x" or "^Vx" (x not NUL) is one escaped unit. */
static size_t r_skip(const char *p) {
  size_t i = 0;
  for (;;) {
    char c = p[i];
    if (c == 0 || c == '.' || c == ' ' || c == '\t') return i;
    i += ((c == '\\' || c == 22) && p[i + 1] != 0) ? 2 : 1;
  } }
