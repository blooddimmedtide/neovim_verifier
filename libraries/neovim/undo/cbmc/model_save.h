// Reduced types for u_update_save_nr: only the fields it uses, names as in nvim/undo_defs.h
// (uh_next is the same pointer/seq union) and nvim/buffer_defs.h.
#include <assert.h>
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>
typedef struct u_header u_header_T;
struct u_header { union { u_header_T *ptr; int seq; } uh_next; int uh_save_nr; };
typedef struct { u_header_T *b_u_newhead; u_header_T *b_u_curhead; int b_u_save_nr_last; int b_u_save_nr_cur; } buf_T;
