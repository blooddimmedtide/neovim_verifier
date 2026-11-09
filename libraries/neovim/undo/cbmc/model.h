// Prelude for the undo-file helpers: the Neovim types they use, copied from the headers named
// below, and a model of FILE as a byte array (reads) plus a capped output log (writes).
// Nothing here is code under test.
#include <assert.h>
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_NONNULL_ARG(...)
#define FUNC_ATTR_UNUSED
#define MAX(X, Y) ((X) > (Y) ? (X) : (Y))   // nvim/macros_defs.h
#define EOF (-1)

typedef int32_t linenr_T;                  // nvim/pos_defs.h
typedef int colnr_T;                       // nvim/pos_defs.h
typedef struct { linenr_T lnum; colnr_T col; colnr_T coladd; } pos_T;   // nvim/pos_defs.h
typedef struct { pos_T vi_start; pos_T vi_end; int vi_mode; colnr_T vi_curswant; } visualinfo_T;
typedef int64_t off_T;                     // nvim/os/fs_defs.h (64-bit off_t)
typedef struct { int uh_seq; } u_header_T; // only the field these functions read (undo_defs.h)
typedef struct buf_T buf_T;

// FILE model. Reads come from in[0..in_len), position in_pos. Writes go to out[0..out_len),
// and each fwrite may fail (nondeterministic), as a full disk can.
#define OUT_CAP 32
typedef struct {
  const uint8_t *in; size_t in_len; size_t in_pos; bool eof;
  uint8_t out[OUT_CAP]; size_t out_len; bool tell_fails;
} FILE;

typedef struct { buf_T *bi_buf; FILE *bi_fp; off_T bi_fsize; } bufinfo_T;   // undo.c

bool nondet_bool(void);
int corruption_calls;   // counts corruption_error() calls
bool writes_may_fail = true;

static inline int getc(FILE *f) {
  if (f->in_pos >= f->in_len) { f->eof = true; return EOF; }
  return f->in[f->in_pos++];
}
static inline int feof(FILE *f) { return f->eof; }
static inline size_t fread(void *buf, size_t size, size_t n, FILE *f) {
  assert(n == 1);   // undo_read always asks for one item
  size_t left = f->in_len - f->in_pos, k = left < size ? left : size;
  memcpy(buf, f->in + f->in_pos, k);
  f->in_pos += k;
  if (k < size) { f->eof = true; return 0; }
  return 1;
}
static inline size_t fwrite(const void *buf, size_t size, size_t n, FILE *f) {
  assert(n == 1);
  if (writes_may_fail && nondet_bool()) return 0;   // write error
  assert(f->out_len + size <= OUT_CAP);   // harness capacity, not a property of the code
  memcpy(f->out + f->out_len, buf, size);
  f->out_len += size;
  return 1;
}
static inline off_T vim_ftell(FILE *f) { return f->tell_fails ? -1 : (off_T)f->in_pos; }
static inline void corruption_error(const char *mesg, const char *file_name) {
  assert(mesg != NULL && file_name != NULL);
  corruption_calls++;
}
// nvim/memory.c: xmallocz never returns NULL (it exits on OOM) and NUL-terminates.
static inline void *xmallocz(size_t size) {
  assert(size < SIZE_MAX);
  char *p = malloc(size + 1);
  p[size] = 0;
  return p;
}
static inline void xfree(void *p) { free(p); }
