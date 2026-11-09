// Model of the environment the copied spellfile.c helpers run in.
// FILE: an in-memory file of `len` bytes read from `pos`, as getc/fread/feof
// behave on a regular file with no I/O error (C11 7.21.7.1, 7.21.8.1, 7.21.10.2).
// Allocator: xmallocz/xfree as in memory.c (malloc never fails: Neovim exits instead).
// slang_T: only the field the proved code touches, with its upstream type.
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#define memchr model_memchr
#define NUL '\000'
#define EOF (-1)
#define VIMSPELLMAGIC "VIMspell"
#define VIMSPELLMAGICL (sizeof(VIMSPELLMAGIC) - 1)
enum { MAXREGIONS = 8, };
enum { SP_TRUNCERROR = -1, SP_FORMERROR = -2, SP_OTHERERROR = -3, };
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_ALWAYS_INLINE

typedef struct { const unsigned char *data; size_t len, pos; bool eof; } FILE;
static int getc(FILE *f) {
  if (f->pos >= f->len) { f->eof = true; return EOF; }
  return f->data[f->pos++];
}
static size_t fread(void *buf, size_t sz, size_t n, FILE *f) {
  __CPROVER_assert(sz == 1, "model: element size 1");
  size_t k = 0;
  while (k < n) {
    if (f->pos >= f->len) { f->eof = true; break; }
    ((unsigned char *)buf)[k++] = f->data[f->pos++];
  }
  return k;
}
static int feof(FILE *f) { return f->eof; }
static void *xmallocz(size_t size) {
  __CPROVER_assert(size + 1 > size, "xmallocz: size + 1 does not wrap");
  char *p = malloc(size + 1);
  p[size] = 0;
  return p;
}
static void xfree(void *p) { free(p); }
// memchr (C11 7.24.5.1): CBMC has no body for it.
static void *memchr(const void *s, int c, size_t n) {
  for (size_t i = 0; i < n; i++) if (((const unsigned char *)s)[i] == (unsigned char)c) return (void *)((const unsigned char *)s + i);
  return NULL;
}
typedef struct { char sl_regions[MAXREGIONS * 2 + 1]; } slang_T;
