// Types and macros for get_undolevel / zero_fmark_additional_data, as Neovim defines them
// (files named per line). buf_T and fmark_T are reduced to the fields these functions use.
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
typedef int64_t OptInt;                       // nvim/types_defs.h
#define NO_LOCAL_UNDOLEVEL (-123456)          // nvim/option_vars.h
#define NMARKS ('z' - 'a' + 1)                // nvim/mark_defs.h
OptInt p_ul;                                  // nvim/option_vars.h: global 'undolevels'
typedef struct { OptInt b_p_ul; } buf_T;      // buffer-local 'undolevels'
typedef struct AdditionalData AdditionalData;
typedef struct { AdditionalData *additional_data; } fmark_T;
static inline void xfree(void *p) { free(p); }   // nvim/memory.c
#define XFREE_CLEAR(ptr) \
  do { \
    /* Take the address to avoid double evaluation. #1375 */ \
    void **ptr_ = (void **)&(ptr); \
    xfree(*ptr_); \
    /* coverity[dead-store] */ \
    *ptr_ = NULL; \
    (void)(*ptr_); \
  } while (0)                                 // nvim/memory.h (verbatim)
