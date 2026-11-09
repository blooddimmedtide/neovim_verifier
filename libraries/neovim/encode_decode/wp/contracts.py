"""Specs for the encode.c / decode.c WP proofs. Written from the documented meaning of each function."""
PRELUDE = r'''
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <limits.h>
#include "mpack/object.h"
#define FUNC_ATTR_NONNULL_ARG(...)
typedef struct {
  int ga_len;                       // current number of items used
  int ga_maxlen;                    // maximum number of items possible
  int ga_itemsize;                  // sizeof(item)
  int ga_growsize;                  // number of items to grow each time
  void *ga_data;                    // pointer to the first item
} garray_T;
typedef enum { VAR_UNLOCKED = 0, VAR_LOCKED = 1, VAR_FIXED = 2 } VarLockStatus;
typedef struct blobvar_S blob_T;
struct blobvar_S {
  garray_T bv_ga;         ///< Growarray with the data.
  int bv_refcount;        ///< Reference count.
  VarLockStatus bv_lock;  ///< VAR_UNLOCKED, VAR_LOCKED, VAR_FIXED.
};

/*@ predicate ga_ok{L}(garray_T *g) =
      \valid(g) && 0 <= g->ga_len <= g->ga_maxlen && g->ga_itemsize == 1
      && \valid((uint8_t *)g->ga_data + (0 .. g->ga_maxlen - 1))
      && \base_addr(g) != \base_addr((char *)g->ga_data); */
/*@ // ga_concat_len (garray.c): trusted contract matching the one proved in ../../garray
    // (PR #4, avoid-arg allocator stubs, smoke tests on). Appends len bytes of s.
    // The new block (if any) never overlaps s: s is a live object the caller passes.
    requires ga_ok(gap) && gap->ga_growsize >= 1;
    requires len <= INT_MAX && gap->ga_len + len + gap->ga_len / 2 + gap->ga_growsize <= INT_MAX;
    requires len > 0 ==> \valid_read(s + (0 .. len - 1));
    requires len > 0 ==> \base_addr(s) != \base_addr((char *)gap->ga_data) && \base_addr(s) != \base_addr(gap);
    assigns gap->ga_len, gap->ga_maxlen, gap->ga_data,
            ((uint8_t *)\at(gap->ga_data, Post))[0 .. \at(gap->ga_maxlen, Post) - 1];
    ensures ga_ok(gap) && gap->ga_len == \old(gap->ga_len) + len;
    ensures \forall integer i; 0 <= i < \old(gap->ga_len) ==>
              ((uint8_t *)gap->ga_data)[i] == \old(((uint8_t *)gap->ga_data)[i]);
    ensures \forall integer i; 0 <= i < len ==>
              ((uint8_t *)gap->ga_data)[\old(gap->ga_len) + i] == \old(((uint8_t *)s)[i]); */
void ga_concat_len(garray_T *const gap, const char *const s, const size_t len);

/*@ // encode_blob_write: append buf[0..len) to the blob's bytes and return len.
    // len <= INT_MAX: the return is (int)len, a signed downcast; callers (msgpack packer
    // writes) pass chunk lengths far below that.
    requires \valid((blob_T *)data) && ga_ok(&((blob_T *)data)->bv_ga);
    requires ((blob_T *)data)->bv_ga.ga_growsize >= 1;
    requires len <= INT_MAX && ((blob_T *)data)->bv_ga.ga_len + len
             + ((blob_T *)data)->bv_ga.ga_len / 2 + ((blob_T *)data)->bv_ga.ga_growsize <= INT_MAX;
    requires len > 0 ==> \valid_read(buf + (0 .. len - 1))
             && \base_addr(buf) != \base_addr((char *)((blob_T *)data)->bv_ga.ga_data)
             && \base_addr(buf) != \base_addr((char *)data);
    assigns ((blob_T *)data)->bv_ga.ga_len, ((blob_T *)data)->bv_ga.ga_maxlen,
            ((blob_T *)data)->bv_ga.ga_data,
            ((uint8_t *)\at(((blob_T *)data)->bv_ga.ga_data, Post))[0 .. \at(((blob_T *)data)->bv_ga.ga_maxlen, Post) - 1];
    ensures \result == len;
    ensures ga_ok(&((blob_T *)data)->bv_ga);
    ensures ((blob_T *)data)->bv_ga.ga_len == \old(((blob_T *)data)->bv_ga.ga_len) + len;
    ensures \forall integer i; 0 <= i < \old(((blob_T *)data)->bv_ga.ga_len) ==>
      ((uint8_t *)((blob_T *)data)->bv_ga.ga_data)[i] == \old(((uint8_t *)((blob_T *)data)->bv_ga.ga_data)[i]);
    ensures \forall integer i; 0 <= i < len ==>
      ((uint8_t *)((blob_T *)data)->bv_ga.ga_data)[\old(((blob_T *)data)->bv_ga.ga_len) + i] == \old(((uint8_t *)buf)[i]); */
int encode_blob_write(void *const data, const char *const buf, const size_t len);

//@ ghost long vp_live;
// XFREE_CLEAR: verbatim from src/nvim/memory.h
#define XFREE_CLEAR(ptr) \
  do { \
    /* Take the address to avoid double evaluation. #1375 */ \
    void **ptr_ = (void **)&(ptr); \
    xfree(*ptr_); \
    /* coverity[dead-store] */ \
    *ptr_ = NULL; \
  } while (0)
/*@ // xfree (memory.c): frees p (NULL allowed). Counted in the ghost live count.
    requires p != \null ==> vp_live > LONG_MIN;
    assigns vp_live;
    ensures vp_live == \old(vp_live) - (p == \null ? 0 : 1); */
void xfree(void *p);

/*@ predicate owns_buf(mpack_token_type_t t) =
      t == MPACK_TOKEN_BIN || t == MPACK_TOKEN_STR || t == MPACK_TOKEN_EXT || t == MPACK_TOKEN_MAP;
    logic integer nfreed{L}(mpack_parser_t *p, integer n) =
      n <= 0 ? 0 : nfreed(p, n - 1)
        + (owns_buf(p->items[n - 1].tok.type) && p->items[n - 1].data[1].p != \null ? 1 : 0);
    lemma nfreed_bound{L}: \forall mpack_parser_t *p, integer n; 0 <= n ==> 0 <= nfreed(p, n) <= n; */
/*@ // typval_parser_error_free: for every node on the parser stack (items[0 .. size-1]) that
    // owns a buffer (BIN/STR/EXT/MAP), free data[1].p and set it to NULL. Nothing else changes.
    requires \valid(parser) && parser->size <= MPACK_MAX_OBJECT_DEPTH + 1;
    requires vp_live >= LONG_MIN + MPACK_MAX_OBJECT_DEPTH + 1;
    assigns parser->items[0 .. parser->size - 1].data[1].p, vp_live;
    ensures \forall integer i; 0 <= i < parser->size ==>
      (owns_buf(parser->items[i].tok.type) ? parser->items[i].data[1].p == \null
       : parser->items[i].data[1].p == \old(parser->items[i].data[1].p));
    ensures vp_live == \old(vp_live) - \old(nfreed(parser, parser->size)); */
void typval_parser_error_free(mpack_parser_t *parser);
'''
CHECKS = []
LOOPS = {
    "typval_parser_error_free": [("  for (uint32_t i = 0;", r"""  /*@ loop invariant 0 <= i <= parser->size;
      loop invariant \forall integer j; 0 <= j < i ==>
        (owns_buf(parser->items[j].tok.type) ? parser->items[j].data[1].p == \null
         : parser->items[j].data[1].p == \at(parser->items[j].data[1].p, Pre));
      loop invariant \forall integer j; i <= j < parser->size ==>
        parser->items[j].data[1].p == \at(parser->items[j].data[1].p, Pre);
      loop invariant \forall integer j; 0 <= j < parser->size ==>
        parser->items[j].tok.type == \at(parser->items[j].tok.type, Pre);
      loop invariant vp_live == \at(vp_live, Pre) - nfreed{Pre}(parser, i);
      loop assigns i, vp_live, parser->items[0 .. parser->size - 1].data[1].p;
      loop variant parser->size - i; */
""")],
}
