// u_entry_T as nvim/undo_defs.h defines it (without U_DEBUG), and the allocators the entry code
// uses, as nvim/memory.c specifies them (never NULL: Neovim exits on OOM; xcalloc zero-fills).
#define FUNC_ATTR_NONNULL_RET
#define CLEAR_POINTER(ptr)  memset((ptr), 0, sizeof(*(ptr)))   // nvim/memory.h
typedef struct u_entry u_entry_T;
struct u_entry {
  u_entry_T *ue_next; linenr_T ue_top; linenr_T ue_bot; linenr_T ue_lcount;
  char **ue_array; linenr_T ue_size;
};
static inline void *xmalloc(size_t size) { void *p = malloc(size); return p; }
static inline void *xcalloc(size_t n, size_t size) {
  assert(size == 0 || n <= SIZE_MAX / size);
  void *p = calloc(n, size); return p;
}
