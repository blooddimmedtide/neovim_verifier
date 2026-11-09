// Reproducer for ga-grow-int-overflow.md: the upstream ga_grow/ga_concat_len text with minimal stubs.
// gcc -O1 -fsanitize=undefined ga-grow-int-overflow-repro.c -o r && ./r   (needs about 3 GB of RAM)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <limits.h>
typedef struct { int ga_len, ga_maxlen, ga_itemsize, ga_growsize; void *ga_data; } garray_T;
#define MAX(a,b) ((a)>(b)?(a):(b))
#define WLOG(...) ((void)0)
#define FUNC_ATTR_NONNULL_ALL
#define _(x) x
static const char e_resulting_text_too_long[]="E1240";
static void emsg(const char*s){fprintf(stderr,"emsg %s\n",s);}
static void *xrealloc(void*p,size_t n){void*r=realloc(p,n?n:1); if(!r){fprintf(stderr,"E342: Out of memory (size %zu), preserve_exit\n",n);exit(1);} return r;}
void ga_set_growsize(garray_T *gap, int growsize)
{
  if (growsize < 1) {
    WLOG("trying to set an invalid ga_growsize: %d", growsize);
    gap->ga_growsize = 1;
  } else {
    gap->ga_growsize = growsize;
  }
}
void ga_init(garray_T *gap, int itemsize, int growsize)
{
  gap->ga_data = NULL;
  gap->ga_maxlen = 0;
  gap->ga_len = 0;
  gap->ga_itemsize = itemsize;
  ga_set_growsize(gap, growsize);
}
void ga_grow(garray_T *gap, int n)
{
  if (gap->ga_maxlen - gap->ga_len >= n) {
    // the garray still has enough space, do nothing
    return;
  }

  if (gap->ga_growsize < 1) {
    WLOG("ga_growsize(%d) is less than 1", gap->ga_growsize);
  }

  // the garray grows by at least growsize
  n = MAX(n, gap->ga_growsize);

  // A linear growth is very inefficient when the array grows big.  This
  // is a compromise between allocating memory that won't be used and too
  // many copy operations. A factor of 1.5 seems reasonable.
  n = MAX(n, gap->ga_len / 2);

  int new_maxlen = gap->ga_len + n;

  size_t new_size = (size_t)gap->ga_itemsize * (size_t)new_maxlen;
  size_t old_size = (size_t)gap->ga_itemsize * (size_t)gap->ga_maxlen;

  // reallocate and clear the new memory
  char *pp = xrealloc(gap->ga_data, new_size);
  memset(pp + old_size, 0, new_size - old_size);

  gap->ga_maxlen = new_maxlen;
  gap->ga_data = pp;
}
void ga_concat_len(garray_T *const gap, const char *restrict s, const size_t len)
  FUNC_ATTR_NONNULL_ALL
{
  if (len == 0) {
    return;
  }
  if (len > (size_t)(INT_MAX - gap->ga_len)) {
    emsg(_(e_resulting_text_too_long));
    return;
  }
  ga_grow(gap, (int)len);
  char *data = gap->ga_data;
  memcpy(data + gap->ga_len, s, len);
  gap->ga_len += (int)len;
}
int main(void){ garray_T ga; ga_init(&ga,1,80);
 size_t big=1500u*1000u*1000u; char *s=calloc(big,1);
 ga_concat_len(&ga,s,big); printf("len=%d maxlen=%d\n",ga.ga_len,ga.ga_maxlen);
 /* fill up to maxlen, then one more byte */
 ga_concat_len(&ga,s,(size_t)(ga.ga_maxlen-ga.ga_len)); printf("len=%d maxlen=%d\n",ga.ga_len,ga.ga_maxlen);
 ga_concat_len(&ga,"x",1); printf("len=%d maxlen=%d\n",ga.ga_len,ga.ga_maxlen); return 0;}
