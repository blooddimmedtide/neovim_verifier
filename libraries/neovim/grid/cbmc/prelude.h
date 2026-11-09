// Minimal declarations so the verbatim grid.c / mbyte.c text compiles alone (x86_64, little-endian).
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
typedef uint32_t schar_T;              // types_defs.h
#define MAX_SCHAR_SIZE 32              // types_defs.h
#define NUL '\0'
typedef int32_t sattr_T;               // types_defs.h
typedef int colnr_T;                   // pos_defs.h
// grid_defs.h ScreenGrid, reduced to the fields these functions touch.
typedef int handle_T;                  // types_defs.h
typedef struct { handle_T handle; schar_T *chars; sattr_T *attrs; colnr_T *vcols; size_t *line_offset; int rows; int cols; } ScreenGrid;
typedef struct { int row_offset, col_offset; ScreenGrid *target; } GridView;
// Model of the glyph cache (map_defs.h Set(glyph)): keys is a flat byte array of n_keys bytes
// holding NUL-terminated glyphs (mh_put_glyph), each shorter than MAX_SCHAR_SIZE (grid.c comment).
struct { struct { uint32_t n_keys; } h; char *keys; } glyph_cache;
int utf_char2bytes(const int c, char *const buf);
#include <limits.h>
// POSIX strnlen (CBMC has no body for it): number of bytes before the first NUL, at most n.
static size_t strnlen(const char *s, size_t n) { size_t i = 0; while (i < n && s[i]) i++; return i; }
#define MIN(a, b) ((a) < (b) ? (a) : (b))   // macros.h
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define schar_from_ascii(x) ((schar_T)(x))   // grid.h, little-endian
// globals.h line buffer (allocated by grid_alloc to linebuf_size cells).
schar_T *linebuf_char; sattr_T *linebuf_attr; colnr_T *linebuf_vcol;
static size_t linebuf_size;
// ui.c, not proved here: the harness records the call (argument recorder, not a contract).
static int rec_calls, rec_grid, rec_row, rec_col;
void ui_grid_cursor_goto(handle_T grid_handle, int new_row, int new_col)
{ rec_calls++; rec_grid = grid_handle; rec_row = new_row; rec_col = new_col; }
