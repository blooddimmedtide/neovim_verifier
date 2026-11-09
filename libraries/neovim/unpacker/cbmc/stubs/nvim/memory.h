// Stub for kvec.h's include: xrealloc as Neovim documents it (never returns NULL;
// on failure Neovim exits). Modelled by realloc with --no-malloc-may-fail.
#include <stdlib.h>
#define REAL_FATTR_NONNULL_ALL
#define REAL_FATTR_NONNULL_RET
#define REAL_FATTR_ALWAYS_INLINE
#define XFREE_CLEAR(ptr) do { void **ptr_ = (void **)&(ptr); xfree(*ptr_); *ptr_ = NULL; } while (0)  // as memory.h
static void xfree(void *p) { free(p); }
static void *xrealloc(void *ptr, size_t size) { return realloc(ptr, size); }
