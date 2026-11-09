// Differential test: the compiled path.c functions (the WP build output, which is the
// pinned text plus ACSL comments gcc ignores) against references written from the doc
// comments. Exhaustive over every string of length 0..6 on a 15-byte alphabet, each in an
// exact-size heap block so ASan catches any read past the NUL. ASCII only: the mbyte.c
// helpers are their ASCII behavior (utfc_ptr2len 1, utf_head_off 0).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int utfc_ptr2len(const char *const p) { return *p ? 1 : 0; }
int utf_head_off(const char *b, const char *p) { (void)b; (void)p; return 0; }
// memory.c strchrsub, verbatim (proved separately: memory/wp)
#include <assert.h>
void strchrsub(char *str, char c, char x)
{
  assert(c != 0);  // NUL in memory.c
  while ((str = strchr(str, c))) {
    *str++ = x;
  }
}
// strings.c vim_strchr for the bytes this test uses (c < 0x80 is the verbatim branch;
// c >= 0x80 searches its 2-byte UTF-8 form as utf_char2bytes gives it)
char *vim_strchr(const char *const string, const int c)
{
  if (c <= 0) return NULL;
  if (c < 0x80) return (char *)strchr(string, c);
  char u8[3] = { (char)(0xC0 | (c >> 6)), (char)(0x80 | (c & 0x3F)), 0 };
  return strstr(string, u8);
}
#include "path_built.c"

static const char AL[] = "/a:\\\"~+.C| -9*`";
static int isal(int c) { return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'); }
static int issch(int c) { return isal(c) || (c >= '0' && c <= '9') || c == '+' || c == '-' || c == '.'; }
static size_t lead(const char *s) { size_t i = 0; while (s[i] == '/') i++; return i; }
static size_t r_tail(const char *s) { size_t t = 0; for (size_t i = 0; s[i]; i++) if (s[i] == '/') t = i + 1; return t; }
static size_t r_next(const char *s) { const char *q = strchr(s, '/'); return q ? (size_t)(q - s) + 1 : strlen(s); }
static size_t r_tws(const char *s) { size_t t = r_tail(s), h = lead(s); while (t > h && s[t - 1] == '/') t--; return t; }
static int r_drive(const char *s, size_t n) {
  return n >= 2 && isal(s[0]) && (s[1] == ':' || s[1] == '|')
         && (n == 2 || s[2] == '/' || s[2] == '\\' || s[2] == '?' || s[2] == '#');
}
static int r_urlk(const char *p) {
  if (p[0] == ':' && p[1] == '/') return 1;
  if (p[0] == ':' && p[1] == '\\' && p[2] == '\\') return 2;
  return 0;
}
static int r_url(const char *s) {
  if (!isal(s[0]) || r_drive(s, strlen(s))) return 0;
  size_t k = 1; while (issch(s[k])) k++;
  if (s[k - 1] == '+' || s[k - 1] == '-' || s[k - 1] == '.') return 0;
  return r_urlk(s + k);
}

// reference from the doc: an unescaped wildcard (UNIX "*?[{", with all also "`'$"), or with
// all a '~' that is not last; a byte is escaped when an odd run of backslashes precedes it
static int r_wild(const char *s, int all) {
  for (size_t i = 0; s[i]; i++) {
    size_t b = 0; while (b < i && s[i - 1 - b] == '\\') b++;
    if (b % 2) continue;
    if (strchr(all ? "*?[{`'$" : "*?[{", s[i])) return 1;
    if (all && s[i] == '~' && s[i + 1]) return 1;
  }
  return 0;
}

static long fails;
#define EXPECT(cond, s) do { if (!(cond)) { if (fails++ < 20) printf("FAIL %s: [%s]\n", #cond, s); } } while (0)

static void one(const char *src, size_t n)
{
  char *s = malloc(n + 1); memcpy(s, src, n + 1);
  EXPECT((size_t)(path_tail(s) - s) == r_tail(s), s);
  EXPECT((size_t)(path_next_component(s) - s) == r_next(s), s);
  EXPECT((size_t)(path_skip_sep(s, true) - s) == lead(s), s);
  EXPECT((size_t)(get_past_head(s) - s) == lead(s), s);
  EXPECT((size_t)(path_tail_with_sep(s) - s) == r_tws(s), s);
  EXPECT(path_is_absolute(s) == (s[0] == '/' || s[0] == '~'), s);
  EXPECT(is_path_head(s) == (s[0] == '/'), s);
  EXPECT(path_with_url(s) == r_url(s), s);
  EXPECT(vim_isAbsName(s) == (r_url(s) != 0 || s[0] == '/' || s[0] == '~'), s);
  EXPECT(path_is_url(s) == r_urlk(s), s);
  EXPECT(vim_backtick(s) == (n >= 2 && s[0] == '`' && s[n - 1] == '`'), s);
  EXPECT(path_has_wildcard(s, false) == r_wild(s, 0), s);
  EXPECT(path_has_wildcard(s, true) == r_wild(s, 1), s);
  for (size_t m = 0; m <= n; m++) {
    EXPECT(path_has_drive_letter(s, m) == r_drive(s, m), s);
    EXPECT(after_pathsep(s, s + m) == (m > 0 && s[m - 1] == '/'), s);
  }
  {
    char *a = malloc(n + 1), *b = malloc(n + 1); memcpy(a, s, n + 1); memcpy(b, s, n + 1);
    path_to_backslash(a); path_to_slash(b);
    for (size_t i = 0; i <= n; i++) {
      EXPECT(a[i] == (s[i] == '/' ? '\\' : s[i]), s);
      EXPECT(b[i] == (r_url(s) == 0 && s[i] == '\\' ? '/' : s[i]), s);
    }
    free(a); free(b);
    char big[MAXPATHL]; memcpy(big, s, n + 1);
    bool r = add_pathsep(big);
    if (n == 0 || s[n - 1] == '/') EXPECT(r && strcmp(big, s) == 0, s);
    else EXPECT(r && big[n] == '/' && big[n + 1] == 0 && memcmp(big, s, n) == 0, s);
  }
#ifdef FIXED
  size_t len; const char *t = invocation_path_tail(s, &len);
  EXPECT(t >= s && t + len <= s + n && (t == s || t[-1] == '/'), s);
#endif
  free(s);
}

int main(void)
{
  char buf[8]; long count = 0;
  for (int c = 0; c < 256; c++) {
    EXPECT(vim_ispathsep(c) == (c == '/'), "c");
    EXPECT(vim_ispathsep_nocolon(c) == (c == '/'), "c");
    EXPECT(vim_ispathlistsep(c) == (c == ':'), "c");
    EXPECT(ascii_isdigit(c) == (c >= '0' && c <= '9'), "c");
  }
  EXPECT(path_head_length() == 1, "");
  EXPECT(strcmp(path_tail(NULL), "") == 0, "NULL");
  // doc examples
  EXPECT(strcmp(path_tail("dir/file.txt"), "file.txt") == 0, "dir/file.txt");
  EXPECT(strcmp(path_tail("dir/"), "") == 0, "dir/");
  { char e[] = "dir///file.txt"; EXPECT(strcmp(path_tail_with_sep(e), "///file.txt") == 0, e); }
  {  // add_pathsep at the MAXPATHL limit
    static char big[MAXPATHL];
    memset(big, 'a', MAXPATHL - 2); big[MAXPATHL - 2] = 0;
    EXPECT(add_pathsep(big) && big[MAXPATHL - 2] == '/' && big[MAXPATHL - 1] == 0, "4094");
    memset(big, 'a', MAXPATHL - 1); big[MAXPATHL - 1] = 0;
    EXPECT(!add_pathsep(big) && big[MAXPATHL - 1] == 0, "4095");
  }
  size_t L = strlen(AL);
  for (size_t n = 0; n <= 6; n++) {
    size_t tot = 1; for (size_t i = 0; i < n; i++) tot *= L;
    for (size_t x = 0; x < tot; x++) {
      size_t y = x;
      for (size_t i = 0; i < n; i++) { buf[i] = AL[y % L]; y /= L; }
      buf[n] = 0; one(buf, n); count++;
    }
  }
  printf("%ld strings, %ld failures\n", count, fails);
  return fails != 0;
}
