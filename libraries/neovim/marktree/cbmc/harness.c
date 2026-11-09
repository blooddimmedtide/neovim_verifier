// CBMC proofs for the marktree.c meta counter functions (bit operations on uint32_t,
// loops of kMTMetaCount = 5 iterations, so a bounded proof is complete).
// mt.c is the WP build's output (verbatim pinned text; CBMC ignores the ACSL comments).
#include "mt.c"
void vp_assert(int c) { __CPROVER_assert(c, "upstream assert()"); }
uint32_t nondet_u32(void);
uint16_t nondet_u16(void);
int nondet_int(void);

// reference, from the doc comments: a key that is not an end key and not invalid
// adds one to each kind its decoration flags name
static uint32_t ref_inc(uint16_t f, int m)
{
  if ((f & MT_FLAG_END) || (f & MT_FLAG_INVALID)) return 0;
  uint16_t b = m == kMTMetaInline ? MT_FLAG_DECOR_VIRT_TEXT_INLINE
             : m == kMTMetaLines ? MT_FLAG_DECOR_VIRT_LINES
             : m == kMTMetaSignHL ? MT_FLAG_DECOR_SIGNHL
             : m == kMTMetaSignText ? MT_FLAG_DECOR_SIGNTEXT : MT_FLAG_DECOR_CONCEAL_LINES;
  return (f & b) ? 1 : 0;
}

void check_meta_describe_key_inc(void)
{
  uint32_t meta[kMTMetaCount], old[kMTMetaCount];
  for (int m = 0; m < kMTMetaCount; m++) old[m] = meta[m] = nondet_u32();
  MTKey k; k.flags = nondet_u16();
  meta_describe_key_inc(meta, &k);
  for (int m = 0; m < kMTMetaCount; m++)
    __CPROVER_assert(meta[m] == (uint32_t)(old[m] + ref_inc(k.flags, m)), "inc: count + flag bit (mod 2^32)");
}

void check_meta_describe_key(void)
{
  uint32_t meta[kMTMetaCount];
  for (int m = 0; m < kMTMetaCount; m++) meta[m] = nondet_u32();
  MTKey k; k.flags = nondet_u16();
  meta_describe_key(meta, k);
  for (int m = 0; m < kMTMetaCount; m++)
    __CPROVER_assert(meta[m] == ref_inc(k.flags, m), "describe: exactly the key's own counts");
}

void check_meta_has(void)
{
  uint32_t count[kMTMetaCount], filter[kMTMetaCount];
  for (int m = 0; m < kMTMetaCount; m++) {
    count[m] = nondet_u32(); filter[m] = nondet_u32();
#ifdef DOC_FILTER  // the documented filter shape: kMTFilterSelect or 0 per kind
    __CPROVER_assume(filter[m] == 0 || filter[m] == UINT32_MAX);
#endif
  }
  bool want = false;
  for (int m = 0; m < kMTMetaCount; m++) want = want || (count[m] & filter[m]) != 0;
  __CPROVER_assert(meta_has(count, filter) == want, "has: some selected kind has a nonzero count");
}
