// FIXED mh_realloc (verified_neovim branch claude/project-thread-ik9odv).
// Annotated standalone copy of map.c's type-generic layer and its int-key
// instance (map_key_impl.c.h with KEY_NAME(x) = x##int, map_value_impl.c.h with
// VAL_NAME = ptr_t). The C text between the markers is the upstream text at
// 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd; build.py checks that removing every
// /*@ ... */ gives back exactly the pinned upstream pieces.
#include "vp_map.h"

// ---- prelude: map_defs.h / map.c macros and types, as upstream defines them ----
// `set` is an ACSL keyword: rename the identifier everywhere (C and ACSL) by the preprocessor.
#define set vset
#define MAX(X, Y) ((X) > (Y) ? (X) : (Y))
typedef void *ptr_t;
typedef struct {
  uint32_t n_buckets;
  uint32_t size;
  uint32_t n_occupied;
  uint32_t upper_bound;
  uint32_t n_keys;  // this is almost always "size", but keys[] could contain ded items..
  uint32_t keys_capacity;
  uint32_t *hash;
} MapHash;
#define MH_TOMBSTONE UINT32_MAX
#define mh_is_empty(h, i) ((h)->hash[i] == 0)
#define mh_is_del(h, i) ((h)->hash[i] == MH_TOMBSTONE)
#define mh_is_either(h, i) ((uint32_t)((h)->hash[i] + 1U) <= 1U)
typedef enum {
  kMHExisting = 0,
  kMHNewKeyDidFit,
  kMHNewKeyRealloc,
} MHPutStatus;
typedef struct { MapHash h; int *keys; } Set_int;
typedef struct { Set_int set; ptr_t *values; } Map_int_ptr_t;
static const ptr_t value_init_ptr_t = NULL;
#define equal_simple(x, y) ((x) == (y))
#define hash_uint32_t(x) (x)
#define equal_uint32_t equal_simple
#define hash_int(x) hash_uint32_t((uint32_t)(x))
#define equal_int equal_simple
#define UPPER_FILL 0.77
#define roundup32(x) (--(x), (x) |= (x)>>1, (x) |= (x)>>2, (x) |= (x)>>4, (x) |= (x)>>8, \
                      (x) |= (x)>>16, ++(x))
#define KEY_NAME(x) x##int
#define SET_TYPE KEY_NAME(Set_)
#define KEY_TYPE KEY_NAME()
#define quasiquote(x, y) x##y
#define VAL_NAME(x) quasiquote(x, ptr_t)
#define after_underscore(x) quasiquote(x, _)
#define MAP_NAME(x) VAL_NAME(after_underscore(KEY_NAME(x)))
#define MAP_TYPE MAP_NAME(Map_)
#define VALUE_TYPE VAL_NAME()
#define INITIALIZER VAL_NAME(value_init_)

/*@ // A well-formed hash index: n_buckets > 0 slots, each EMPTY (0), deleted
    // (TOMBSTONE) or 1 + an index into keys[0 .. n_keys - 1].
    predicate slot_ok(MapHash *h, integer i) =
      h->hash[i] == 0 || h->hash[i] == MH_TOMBSTONE || 1 <= h->hash[i] <= h->n_keys;
    predicate wf_hash(Set_int *s) =
      s->h.n_buckets > 0 && s->h.n_buckets <= 2147483648 && (s->h.n_buckets & (s->h.n_buckets - 1)) == 0 &&
      4294967296 % s->h.n_buckets == 0 && \valid(s->h.hash + (0 .. s->h.n_buckets - 1)) &&
      s->h.n_keys < MH_TOMBSTONE &&
      \valid(s->keys + (0 .. s->h.n_keys - 1)) &&
      \separated(s->h.hash + (0 .. s->h.n_buckets - 1), s->keys + (0 .. s->h.n_keys - 1), s) &&
      \forall integer i; 0 <= i < s->h.n_buckets ==> slot_ok(&s->h, i);
    // slot i holds key k
    predicate holds(Set_int *s, integer i, int k) =
      1 <= s->h.hash[i] <= s->h.n_keys && s->keys[s->h.hash[i] - 1] == k;
*/

/*@ logic integer ru(integer x) =
      \let a0 = x - 1; \let a1 = a0 | (a0 >> 1); \let a2 = a1 | (a1 >> 2);
      \let a3 = a2 | (a2 >> 4); \let a4 = a3 | (a3 >> 8); \let a5 = a4 | (a4 >> 16); a5 + 1;
*/
/*@ ghost
  /@ // Checked with Z3 on 32-bit vectors by lemmas.smt2 (all x in range, exhaustive by solver).
     requires 16 <= x <= 2147483648;
     assigns \nothing;
     ensures x <= ru(x) <= 2147483648 && ru(x) < 2 * x && (ru(x) & (ru(x) - 1)) == 0;
  @/
  void roundup_lemma(uint32_t x);
*/

/*@ ghost
  /@ // Checked with Z3 on bit-vectors by lemmas.smt2.
     requires 1 <= n <= 2147483648 && (n & (n - 1)) == 0 && 0 <= x <= 4294967295;
     assigns \nothing;
     ensures (x & (n - 1)) == x % n && 0 <= (x & (n - 1)) < n;
  @/
  void mask_lemma(uint64_t x, uint64_t n);
*/
/*@ ghost
  /@ // One quadratic probe step from step p to p + 1. Checked with Z3 on bit-vectors
     // by lemmas_probe.smt2 (s = p + 1 there).
     requires 1 <= n <= 2147483648 && (n & (n - 1)) == 0;
     requires i0 < n && last < n && 0 <= p <= 2 * n - 2;
     requires i0 == ((last + p * (p + 1) / 2) & (n - 1));
     assigns \nothing;
     ensures (((i0 + (p + 1) % 4294967296) % 4294967296) & (n - 1)) == ((last + (p + 1) * (p + 2) / 2) & (n - 1));
     ensures p + 1 == 2 * n - 1 ==> ((last + (p + 1) * (p + 2) / 2) & (n - 1)) == last;
  @/
  void probe_lemma(uint64_t i0, uint64_t p, uint64_t last, uint64_t n);
*/

/*@ ghost uint32_t vp_slot[4294967295]; */  // ghost: slot found for each rehashed key

// ---- upstream map.c ----

/*@ requires \valid(h);
    requires h->hash == \null || \freeable(h->hash);
    assigns *h;
    exits vp_oom || n_min_buckets > 2147483648;   // fixed: abort() instead of wrapping
    ensures h->n_buckets >= 16 && h->n_buckets >= n_min_buckets;
    ensures h->n_buckets <= 2147483648;
    ensures (h->n_buckets & (h->n_buckets - 1)) == 0;  // a power of two
    ensures \valid(h->hash + (0 .. h->n_buckets - 1));
    ensures \forall integer i; 0 <= i < h->n_buckets ==> h->hash[i] == 0;
    ensures h->n_occupied == 0 && h->size == 0;
    ensures h->n_keys == \old(h->n_keys) && h->keys_capacity == \old(h->keys_capacity);
*/
void mh_realloc(MapHash *h, uint32_t n_min_buckets)
{
  xfree(h->hash);
  uint32_t n_buckets = n_min_buckets < 16 ? 16 : n_min_buckets;
  if (n_buckets > ((uint32_t)1 << 31)) {
    // 2^31 is the largest power of two in uint32_t: roundup32 would wrap to 0
    abort();
  }
  /*@ ghost uint32_t x0 = n_buckets; */
  roundup32(n_buckets);
  /*@ assert n_buckets == ru(x0); */
  /*@ ghost roundup_lemma(x0); */
  // sets all buckets to EMPTY
  h->hash = xcalloc(n_buckets, sizeof *h->hash) /*@ ghost (&h->n_buckets) */;
  /*@ assert \base_addr(h->hash) != \base_addr(h) && \separated(h, h->hash + (0 .. n_buckets - 1)) && \separated(&h->n_occupied, &h->size, &h->n_buckets, &h->upper_bound, h->hash + (0 .. n_buckets - 1)) && \forall integer i; 0 <= i < n_buckets ==> h->hash[i] == 0; */
  /*@ ghost VpL: ; */
  h->n_occupied = h->size = 0;
  h->n_buckets = n_buckets;
  h->upper_bound = (uint32_t)(h->n_buckets * UPPER_FILL + 0.5);
  /*@ assert h->hash == \at(h->hash, VpL) && h->n_buckets == n_buckets; */
  /*@ assert \forall integer i; 0 <= i < n_buckets ==> h->hash[i] == \at(h->hash[i], VpL); */
}

