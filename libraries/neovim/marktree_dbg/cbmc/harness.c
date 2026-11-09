/* mt_dbg_id from src/nvim/marktree.c @ 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd, copied verbatim. */
#include <stdint.h>
#include <assert.h>
static inline uint64_t mt_dbg_id(uint64_t id)
{
  return (id >> 1) & 0xffffffff;
}
uint64_t nd64(void);
/* Spec: the debug id is bits 1..32 of the lookup key, i.e. floor(x/2) mod 2^32. */
void check_dbg_id(void) { uint64_t x = nd64(); assert(mt_dbg_id(x) == (x / 2) % 4294967296u); }
