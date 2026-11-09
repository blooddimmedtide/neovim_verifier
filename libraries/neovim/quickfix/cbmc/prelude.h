// Minimal stand-ins for the Neovim headers the errorformat code uses.
#include <stdbool.h>
#include <stdint.h>
#include <assert.h>
#include <stddef.h>
#include <string.h>
#define FUNC_ATTR_NONNULL_ALL
#define NUL '\000'
#define OK 1
#define FAIL 0
#define _(x) (x)
#define STRCPY(d, s) strcpy((char *)(d), (char *)(s))
#define FMT_PATTERNS 14
typedef struct regprog regprog_T;
typedef struct efm_S efm_T;
struct efm_S {
  regprog_T *prog;
  efm_T *next;
  char addr[FMT_PATTERNS];
  char prefix;
  char flags;
  int conthere;
};
// Messages only print: no effect on the proved properties.
static void semsg(const char *fmt, ...) { (void)fmt; }
static void emsg(const char *s) { (void)s; }
// strings.c vim_strchr: c <= 0 -> NULL; c < 0x80 -> strchr. For c >= 0x80 it searches the
// UTF-8 encoding of c (lead byte >= 0xC2); every call site here passes an ASCII-only literal,
// so the result is NULL. The stub returns NULL directly.
static char *vim_strchr(const char *const string, const int c) {
  if (c <= 0 || c >= 0x80) return NULL;
  return strchr(string, c);
}
