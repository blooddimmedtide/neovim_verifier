// CBMC harness for push_additional_data: the builder holds an AdditionalData header
// followed by the raw bytes of nitems skipped ShaDa map entries; nbytes is documented by
// its use in shada.c (mpack_raw(src->data, src->nbytes, ...)) as the byte count after it.
#include UNPACKER_C
#include <assert.h>
size_t nondet_size(void);
uint32_t nondet_u32(void);
#ifndef MAXLEN
#define MAXLEN ((size_t)1 << 40)
#endif

void h_push_additional_data(void)
{
  AdditionalDataBuilder ad;
  ad.size = nondet_size(); ad.capacity = nondet_size();
  __CPROVER_assume(ad.size <= ad.capacity && ad.capacity < MAXLEN);
  __CPROVER_assume(ad.size == 0 || ad.size >= sizeof(AdditionalData));
  ad.items = ad.capacity ? malloc(ad.capacity) : NULL;
  uint32_t n0 = 0;
  if (ad.size) {
    AdditionalData *h = (AdditionalData *)ad.items;
    // builder invariant before the call
    __CPROVER_assume((size_t)h->nbytes == ad.size - sizeof(AdditionalData));
    n0 = h->nitems;
    // one builder collects the items of one msgpack map or array, so at most 2^32 - 1
    __CPROVER_assume(n0 < UINT32_MAX);
  }
  size_t old = ad.size;
  size_t size = nondet_size();
  __CPROVER_assume(size < MAXLEN);
  char *data = malloc(size);
  size_t k = nondet_size();
  __CPROVER_assume(k < size);
  char dk = data[k];
  push_additional_data(&ad, data, size);
  AdditionalData *a = (AdditionalData *)ad.items;
  size_t base = old ? old : sizeof(AdditionalData);
  assert(ad.size == base + size);
  assert(a->nitems == n0 + 1);
  assert(ad.items[base + k] == dk);
  // invariant after the call: nbytes counts every byte after the header
  assert((size_t)a->nbytes == ad.size - sizeof(AdditionalData));
}
