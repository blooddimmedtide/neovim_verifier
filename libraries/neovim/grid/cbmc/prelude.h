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
// grid_defs.h types, reduced to the fields grid_adjust touches.
typedef struct { int dummy; } ScreenGrid;
typedef struct { int row_offset, col_offset; ScreenGrid *target; } GridView;
// Model of the glyph cache (map_defs.h Set(glyph)): keys is a flat byte array of n_keys bytes
// holding NUL-terminated glyphs (mh_put_glyph), each shorter than MAX_SCHAR_SIZE (grid.c comment).
struct { struct { uint32_t n_keys; } h; char *keys; } glyph_cache;
int utf_char2bytes(const int c, char *const buf);
#include <limits.h>
// POSIX strnlen (CBMC has no body for it): number of bytes before the first NUL, at most n.
static size_t strnlen(const char *s, size_t n) { size_t i = 0; while (i < n && s[i]) i++; return i; }
