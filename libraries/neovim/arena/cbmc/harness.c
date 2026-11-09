// CBMC harnesses for the arena allocator in src/nvim/memory.c.
// The upstream text is pasted in verbatim by build.py (arena.c); nothing here
// is derived from its code. Spec, written from the comments in memory.c and
// memory_defs.h and from what callers rely on (msgpack unpacker, kvec):
//  S1 arena_align_offset(off): smallest multiple of 8 that is >= off.
//  S2 arena_alloc(a, n, align) on a well-formed arena returns n writable bytes,
//     8-aligned when align, never overlapping a block header or any earlier
//     allocation from the same arena still live, and leaves the arena well formed.
//  S3 arena_allocz(a, n): n+1 writable bytes, byte n is NUL.
//  S4 arena_memdupz(a, buf, n): copy of buf[0..n) then NUL. arena_strdup likewise.
//  S5 alloc_block / free_block / arena_finish / arena_mem_free /
//     arena_free_reuse_blks: no leak, no double free, no use after free; after
//     arena_finish the arena is empty. The reuse list never exceeds REUSE_MAX.
// Well formed (W): cur_blk == NULL, pos == size == 0; or cur_blk is the start of
// a live ARENA_BLOCK_SIZE object, size == ARENA_BLOCK_SIZE, 8 <= pos <= size.
#include "arena.c"

// xmalloc never returns NULL: on failure it exits (preserve_exit). We model
// failure for sizes past 2^40 as exit; smaller ones succeed with an exact-size
// object so any out-of-bounds access fails the pointer checks.
void *xmalloc(size_t size)
{
  if (size > ((size_t)1 << 40)) { __CPROVER_assume(0); }
  void *p = malloc(size == 0 ? 1 : size);
  __CPROVER_assume(p != NULL);
  return p;
}
void xfree(void *p) { free(p); }

size_t nondet_size(void);
bool nondet_bool(void);
uint64_t nondet_u64(void);

#ifndef SIZE_LIMIT
// Upstream precondition needed for S2 (see findings/arena-alloc-size-wrap.md).
# define SIZE_LIMIT (SIZE_MAX - ARENA_BLOCK_SIZE)
#endif

static bool wellformed(const Arena *a)
{
  if (a->cur_blk == NULL) return a->pos == 0 && a->size == 0;
  return __CPROVER_POINTER_OFFSET(a->cur_blk) == 0
         && __CPROVER_OBJECT_SIZE(a->cur_blk) == ARENA_BLOCK_SIZE
         && a->size == ARENA_BLOCK_SIZE && a->pos >= 8 && a->pos <= a->size;
}

static bool disjoint(const char *p, size_t n, const char *q, size_t m)
{
  if (__CPROVER_POINTER_OBJECT(p) != __CPROVER_POINTER_OBJECT(q)) return true;
  size_t po = __CPROVER_POINTER_OFFSET(p), qo = __CPROVER_POINTER_OFFSET(q);
  return po + n <= qo || qo + m <= po;
}

#ifdef H_ALIGN
void harness(void)
{
  uint64_t off = nondet_u64();
  __CPROVER_assume(off <= UINT64_MAX - 7);
  size_t r = arena_align_offset(off);
  assert(r % 8 == 0 && r >= off && r - off < 8);
}
#endif

#ifdef H_ALLOC
#ifndef NALLOC
# define NALLOC 3
#endif
void harness(void)
{
  Arena a = ARENA_EMPTY;
  char *p[NALLOC]; size_t n[NALLOC];
  for (int i = 0; i < NALLOC; i++) {
    n[i] = nondet_size();
    __CPROVER_assume(n[i] <= SIZE_LIMIT);
    bool al = nondet_bool();
    p[i] = arena_alloc(&a, n[i], al);
    assert(wellformed(&a));
    assert(p[i] != NULL);
    assert(__CPROVER_w_ok(p[i], n[i]));
    assert(__CPROVER_POINTER_OFFSET(p[i]) >= sizeof(struct consumed_blk));  // header untouched
    if (al) assert(__CPROVER_POINTER_OFFSET(p[i]) % 8 == 0);
    for (int j = 0; j < i; j++) assert(disjoint(p[i], n[i], p[j], n[j]));
  }
  arena_mem_free(arena_finish(&a));
  arena_free_reuse_blks();
}
#endif

#ifdef H_LIFE
void harness(void)
{
  for (int round = 0; round < 2; round++) {
    Arena a = ARENA_EMPTY;
    int k = 0;
    while (nondet_bool() && k < 3) {
      size_t n = nondet_size();
      __CPROVER_assume(n <= 3 * ARENA_BLOCK_SIZE);
      char *p = arena_alloc(&a, n, nondet_bool());
      if (n) { p[0] = 1; p[n - 1] = 2; }
      k++;
    }
    ArenaMem m = arena_finish(&a);
    assert(a.cur_blk == NULL && a.pos == 0 && a.size == 0);
    arena_mem_free(m);
    assert(arena_reuse_blk_count <= REUSE_MAX);
  }
  // also a NULL arena: global allocation the caller frees
  size_t n = nondet_size(); __CPROVER_assume(n <= 64);
  char *g = arena_alloc(NULL, n, nondet_bool());
  assert(__CPROVER_w_ok(g, n));
  xfree(g);
  arena_free_reuse_blks();
  assert(arena_reuse_blk_count == 0);
}
#endif

#ifdef H_DUP
#ifndef LEN
# define LEN 4
#endif
void harness(void)
{
  Arena a = ARENA_EMPTY;
  bool use_arena = nondet_bool();
  Arena *ap = use_arena ? &a : NULL;
  char *buf = malloc(LEN + 1);
  __CPROVER_assume(buf != NULL);
  size_t i = nondet_size(); __CPROVER_assume(i < LEN);
  // allocz
  char *z = arena_allocz(ap, LEN);
  assert(__CPROVER_w_ok(z, LEN + 1) && z[LEN] == '\0');
  // memdupz (buf has exactly LEN bytes that are read)
  char *d = arena_memdupz(ap, buf, LEN);
  assert(__CPROVER_w_ok(d, LEN + 1) && d[LEN] == '\0' && d[i] == buf[i]);
  // strdup: buf is a string of length LEN
  for (size_t k = 0; k < LEN; k++) __CPROVER_assume(buf[k] != '\0');
  buf[LEN] = '\0';
  char *s = arena_strdup(ap, buf);
  assert(__CPROVER_w_ok(s, LEN + 1) && s[LEN] == '\0' && s[i] == buf[i]);
  if (!use_arena) { xfree(z); xfree(d); xfree(s); }
  else assert(disjoint(z, LEN + 1, d, LEN + 1) && disjoint(d, LEN + 1, s, LEN + 1));
  free(buf);
  arena_mem_free(arena_finish(&a));
  arena_free_reuse_blks();
}
#endif
