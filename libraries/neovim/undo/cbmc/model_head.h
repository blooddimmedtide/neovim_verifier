// Reduced types for u_get_headentry / u_getbot: only the fields they use, names as in
// nvim/undo_defs.h and nvim/buffer_defs.h. iemsg (internal error message) only counts calls.
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef int32_t linenr_T;                                   // nvim/pos_defs.h
typedef struct u_entry u_entry_T;
struct u_entry { linenr_T ue_top; linenr_T ue_bot; linenr_T ue_lcount; linenr_T ue_size; };
typedef struct { u_entry_T *uh_entry; u_entry_T *uh_getbot_entry; } u_header_T;
typedef struct { linenr_T ml_line_count; } memline_T;
typedef struct { u_header_T *b_u_newhead; memline_T b_ml; bool b_u_synced; } buf_T;
int iemsg_calls;
static inline void iemsg(const char *s) { assert(s != NULL); iemsg_calls++; }
#define _(x) (x)
static const char e_undo_list_corrupt[] = "E439: Undo list corrupt";
static const char e_undo_line_missing[] = "E440: Undo line missing";
