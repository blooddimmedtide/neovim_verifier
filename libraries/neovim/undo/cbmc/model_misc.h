// Reduced types for u_clearline / u_update_named_mark: only the fields they use, names as in
// nvim/undo_defs.h, nvim/buffer_defs.h, nvim/mark_defs.h. XFREE_CLEAR copied from nvim/memory.h.
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
typedef int32_t linenr_T;
typedef int colnr_T;
#define NMARKS ('z' - 'a' + 1)
typedef struct { linenr_T lnum; colnr_T col; colnr_T coladd; } pos_T;
typedef struct { pos_T mark; int fnum; } fmark_T;
typedef struct u_header u_header_T;
struct u_header { fmark_T uh_namedm[NMARKS]; };
typedef struct { u_header_T *b_u_newhead; u_header_T *b_u_curhead; char *b_u_line_ptr; linenr_T b_u_line_lnum; } buf_T;
static inline void xfree(void *p) { free(p); }
#define XFREE_CLEAR(ptr) \
  do { \
    /* Take the address to avoid double evaluation. #1375 */ \
    void **ptr_ = (void **)&(ptr); \
    xfree(*ptr_); \
    /* coverity[dead-store] */ \
    *ptr_ = NULL; \
    (void)(*ptr_); \
  } while (0)
