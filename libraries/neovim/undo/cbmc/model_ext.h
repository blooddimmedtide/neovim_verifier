// Extmark undo types copied from nvim/extmark.h and nvim/extmark_defs.h (field names and order as
// upstream, needed for the sizes the code writes and reads), and the allocators as nvim/memory.c
// specifies them (never NULL; xcalloc zero-fills).
typedef ptrdiff_t bcount_t;                                   // nvim/extmark_defs.h
typedef struct { int start_row; colnr_T start_col; int old_row; colnr_T old_col; int new_row;
  colnr_T new_col; bcount_t start_byte; bcount_t old_byte; bcount_t new_byte; } ExtmarkSplice;
typedef struct { int start_row; int start_col; int extent_row; int extent_col; int new_row;
  int new_col; bcount_t start_byte; bcount_t extent_byte; bcount_t new_byte; } ExtmarkMove;
typedef struct { uint64_t mark; int undo_row; colnr_T undo_col; int redo_row; colnr_T redo_col;
  bool invalidated; } ExtmarkSavePos;
typedef enum { kExtmarkSplice, kExtmarkMove, kExtmarkUpdate, kExtmarkSavePos, kExtmarkClear, } UndoObjectType;
typedef struct undo_object ExtmarkUndoObject;
struct undo_object { UndoObjectType type;
  union { ExtmarkSplice splice; ExtmarkMove move; ExtmarkSavePos savepos; } data; };
#define UF_ENTRY_MAGIC         0xf518                         // undo.c
static inline void *xmalloc(size_t size) { return malloc(size); }
static inline void *xcalloc(size_t n, size_t size) { return calloc(n, size); }
