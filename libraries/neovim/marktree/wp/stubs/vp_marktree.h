// Prelude for marktree.c leaf functions: Neovim's types copied as they are declared
// (build.py checks each line against the pinned headers). DecorInlineData is opaque here:
// no proved function reads it.
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "vp_string.h"
/*@ requires c != 0; assigns \nothing; */
void vp_assert(int c);
#define assert(e) vp_assert((e) ? 1 : 0)
#define MT_BRANCH_FACTOR 10  // enum constant in marktree_defs.h
typedef struct { void *opaque; } DecorInlineData;
typedef struct mtnode_s MTNode;
typedef struct {
  int32_t row;
  int32_t col;
} MTPos;
typedef enum {
  kMTMetaInline,
  kMTMetaLines,
  kMTMetaSignHL,
  kMTMetaSignText,
  kMTMetaConcealLines,
  kMTMetaCount,  // sentinel, must be last
} MetaIndex;
typedef const uint32_t *MetaFilter;
typedef struct {
  MTPos pos;
  uint32_t ns;
  uint32_t id;
  uint16_t flags;
  DecorInlineData decor_data;  // "ext" tag in flags
} MTKey;
typedef struct { size_t size; size_t capacity; uint64_t *items; uint64_t init_array[4]; } Intersection;
struct mtnode_s {
  int32_t n;
  int16_t level;
  int16_t p_idx;  // index in parent
  Intersection intersect;
  MTNode *parent;
  MTKey key[2 * MT_BRANCH_FACTOR - 1];
};
#define kv_A(v, i) ((v).items[(i)])
#define kv_size(v) ((v).size)
#define MT_FLAG_REAL (((uint16_t)1) << 0)
#define MT_FLAG_END (((uint16_t)1) << 1)
#define MT_FLAG_INVALID (((uint16_t)1) << 6)
#define MT_FLAG_DECOR_SIGNTEXT (((uint16_t)1) << 9)
#define MT_FLAG_DECOR_SIGNHL (((uint16_t)1) << 10)
#define MT_FLAG_DECOR_VIRT_LINES (((uint16_t)1) << 11)
#define MT_FLAG_DECOR_VIRT_TEXT_INLINE (((uint16_t)1) << 12)
#define MT_FLAG_DECOR_CONCEAL_LINES (((uint16_t)1) << 13)
#define MT_FLAG_RIGHT_GRAVITY (((uint16_t)1) << 14)
#define MT_FLAG_LAST (((uint16_t)1) << 15)
#define mt_generic_cmp(a, b) (((b) < (a)) - ((a) < (b)))
#define MT_MAX_DEPTH 20  // enum constant in marktree_defs.h
typedef struct {
  MTPos pos;
  int lvl;
  MTNode *x;
  int i;
  struct {
    int oldcol;
    int i;
  } s[MT_MAX_DEPTH];

  size_t intersect_idx;
  MTPos intersect_pos;
  MTPos intersect_pos_x;
} MarkTreeIter;
#define rawkey(itr) ((itr)->x->key[(itr)->i])
