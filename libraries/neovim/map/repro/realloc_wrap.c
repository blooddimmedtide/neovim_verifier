// Runs upstream mh_realloc (text copied from src/nvim/map.c at 7b87ce8) on the
// size mh_put_* requests once a table of 2^31 buckets fills: n_buckets + 1.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef struct { uint32_t n_buckets, size, n_occupied, upper_bound, n_keys, keys_capacity; uint32_t *hash; } MapHash;
static void xfree(void *p) { free(p); }
static void *xcalloc(size_t n, size_t s) { printf("xcalloc(%zu, %zu)\n", n, s); return calloc(n ? n : 1, s); }
#define UPPER_FILL 0.77
#define roundup32(x) (--(x), (x) |= (x)>>1, (x) |= (x)>>2, (x) |= (x)>>4, (x) |= (x)>>8, \
                      (x) |= (x)>>16, ++(x))
void mh_realloc(MapHash *h, uint32_t n_min_buckets)
{
  xfree(h->hash);
  uint32_t n_buckets = n_min_buckets < 16 ? 16 : n_min_buckets;
  roundup32(n_buckets);
  // sets all buckets to EMPTY
  h->hash = xcalloc(n_buckets, sizeof *h->hash);
  h->n_occupied = h->size = 0;
  h->n_buckets = n_buckets;
  h->upper_bound = (uint32_t)(h->n_buckets * UPPER_FILL + 0.5);
}
int main(void)
{
  MapHash h = { 0 };
  mh_realloc(&h, 2147483648u + 1);   // what mh_put asks for when n_buckets == 2^31
  printf("n_buckets=%u upper_bound=%u mask=%u\n", h.n_buckets, h.upper_bound, h.n_buckets - 1);
  return h.n_buckets == 0 ? 1 : 0;
}
