"""ACSL contracts for hashtab.c, written from the doc comments of hashtab.c and
hashtab_defs.h. A table is described by its array, its mask (size - 1, a power of two
minus one) and the invariant `ht_ok` that every function keeps."""

import bvlemmas

FA = "(size_t)((size_t)(4 * {b}) + 1)"                       # the multiplier 4b + 1
VAL = "(size_t)((size_t)((size_t)((size_t)(4 * {b}) + 1) * {x}) + {b})"   # (4b+1)*x + b

LOGIC = r"""
/*@ // mask + 1 is a power of two, at least HT_INIT_SIZE, at most 2^60
    // (the m == 15 case is true anyway; it saves provers from computing 15 & 16)
    predicate tmask(integer m) = (m == 15 || (m & (m + 1)) == 0) && 15 <= m <= 1152921504606846975;
    // the probe sequence of hash_lookup / hash_may_resize for hash h: step 0 is h & m,
    // then idx = 5 * idx + perturb + 1 with perturb = h, h >> 5, h >> 10, ...
    logic integer pert(integer h, integer n) = n <= 0 ? h : pert(h, n - 1) >> 5;
    logic integer pidx(integer h, integer m, integer n) =
      n <= 0 ? (h & m) : (size_t)((size_t)((size_t)(5 * pidx(h, m, n - 1)) + pert(h, n - 1)) + 1);
    logic integer slot(integer h, integer m, integer n) = pidx(h, m, n) & m;
    predicate isused(char *k) = k != \null && k != &hash_removed;
    // number of used / non-empty (used or removed) items among a[0 .. n-1]
    logic integer nused{L}(hashitem_T *a, integer n) =
      n <= 0 ? 0 : nused(a, n - 1) + (isused(a[n - 1].hi_key) ? 1 : 0);
    logic integer nfilled{L}(hashitem_T *a, integer n) =
      n <= 0 ? 0 : nfilled(a, n - 1) + (a[n - 1].hi_key != \null ? 1 : 0);
    // steps 0 .. n-1 of the probe sequence for h meet no never-used item
    predicate nonull{L}(hashitem_T *a, integer m, integer h, integer n) =
      \forall integer k; 0 <= k < n ==> a[slot(h, m, k)].hi_key != \null;
    // item i is found by probing for h: some step reaches i before any never-used item
    predicate reach{L}(hashitem_T *a, integer m, integer h, integer i) =
      \exists integer n; 0 <= n && slot(h, m, n) == i && nonull(a, m, h, n);
    // hash_hash_len: hash of the n bytes s[0 .. n-1]
    logic integer hl{L}(char *s, integer n) =
      n <= 0 ? 0 : n == 1 ? (unsigned char)s[0] : (size_t)((size_t)(hl(s, n - 1) * 101) + (unsigned char)s[n - 1]);
    // s is the key key[0 .. len-1]: the same bytes, then a NUL
    predicate keq{L}(char *s, char *key, integer len) =
      (\forall integer i; 0 <= i < len ==> s[i] == key[i]) && s[len] == 0;
    // the bytes before a string's NUL are not NUL
    lemma str_nz{L}: \forall char *b, integer m, n; str_len(b, m) && 0 <= n < m ==> b[n] != 0;
    lemma keq_short{L}: \forall char *a, char *b, integer n, m; str_len(b, m) && keq(b, a, n) && 0 <= n ==> !(n < m);
    lemma keq_long{L}: \forall char *a, char *b, integer n, m; str_len(a, n) && str_len(b, m) && keq(b, a, n) && 0 <= m ==> !(m < n);
    // a string equal to another up to its own NUL is that string
    lemma keq_flip{L}: \forall char *a, char *b, integer n; str_len(a, n) && keq(b, a, n) ==> keq(a, b, n);
    lemma keq_sym{L}: \forall char *a, char *b, integer n, m; str_len(a, n) && str_len(b, m) && keq(b, a, n)
      ==> n == m && keq(a, b, m);
    // item i holds a key: a string, its hash, and it is found by probing
    predicate item_ok{L}(hashitem_T *a, integer m, integer i) =
      \exists integer n; str_len(a[i].hi_key, n) && n < PTRDIFF_MAX
        && a[i].hi_hash == hl(a[i].hi_key, n) && reach(a, m, a[i].hi_hash, i);
    // no key twice
    predicate distinct{L}(hashitem_T *a, integer m) =
      \forall integer i, j, n; 0 <= i <= m && 0 <= j <= m && i != j && isused(a[i].hi_key)
        && isused(a[j].hi_key) && str_len(a[i].hi_key, n) ==> !keq(a[j].hi_key, a[i].hi_key, n);
    // a well-formed table, except that it may be full (hash_may_resize's input after an add)
    predicate ht_base{L}(hashtab_T *ht) =
      \valid(ht) && tmask(ht->ht_mask) && \valid(ht->ht_array + (0 .. ht->ht_mask))
      && (ht->ht_array == &ht->ht_smallarray[0] <==> ht->ht_mask == HT_INIT_SIZE - 1)
      && (ht->ht_array != &ht->ht_smallarray[0] ==> \base_addr(ht->ht_array) != \base_addr(ht))
      && ht->ht_used == nused(ht->ht_array, ht->ht_mask + 1)
      && ht->ht_filled == nfilled(ht->ht_array, ht->ht_mask + 1)
      && (\forall integer i; 0 <= i <= ht->ht_mask && isused(ht->ht_array[i].hi_key) ==> item_ok(ht->ht_array, ht->ht_mask, i))
      && distinct(ht->ht_array, ht->ht_mask);
    // a well-formed table (what hash_init creates and every function keeps): it has a
    // never-used item, so probing stops
    predicate ht_ok{L}(hashtab_T *ht) = ht_base(ht) && ht->ht_filled <= ht->ht_mask;
    // the table holds key pointer k with hash h
    predicate has{L}(hashtab_T *ht, char *k, integer h) = isused(k) && \exists integer i;
      0 <= i <= ht->ht_mask && ht->ht_array[i].hi_key == k && ht->ht_array[i].hi_hash == h;
    // hash_may_resize: the size the table needs for `used` items (minitems mi)
    logic integer msz(integer used, integer mi) =
      mi == 0 ? (used > 1000 ? used * 2 : used * 4) : ((used > mi ? used : mi) * 3 + 1) / 2;
    // s is the smallest power of two that is at least 16 and at least m
    predicate fit(integer s, integer m) =
      16 <= s && (s == 16 || (s & (s - 1)) == 0) && m <= s && (s == 16 || s / 2 < m);
    // hash_may_resize leaves the table as it is (when not locked)
    predicate keep{L}(hashtab_T *ht, integer mi) =
      (mi == 0 && ((ht->ht_filled < HT_INIT_SIZE - 1 && ht->ht_array == &ht->ht_smallarray[0])
                   || (ht->ht_filled * 3 < (ht->ht_mask + 1) * 2 && ht->ht_used > (ht->ht_mask + 1) / 5)))
      || (fit(ht->ht_mask + 1, msz(ht->ht_used, mi)) && ht->ht_mask + 1 != 16
          && ht->ht_filled * 3 < (ht->ht_mask + 1) * 2);
    // 5^n modulo 2^64
    logic integer p5(integer n) = n <= 0 ? 1 : (size_t)(5 * p5(n - 1));
*/
""" + bvlemmas.acsl(["bv_unfive", "bv_assoc5", "bv_mask_le"]) + r"""
/*@ lemma p5_range: \forall integer n; 0 <= p5(n) <= 18446744073709551615;
    lemma p5_unfive: \forall integer n; 1 <= n ==> p5(n - 1) == (size_t)(p5(n) * 14757395258967641293);
    lemma slot_range: \forall integer h, m, n; 0 <= h <= 18446744073709551615 && 0 <= m <= 18446744073709551615
      ==> 0 <= slot(h, m, n) <= m;
    // filling items keeps every probe path's items non-empty
    lemma nonull_grow{L1, L2}: \forall hashitem_T *a, integer m, h, n; tmask(m) && 0 <= h <= 18446744073709551615
      && (\forall integer j; 0 <= j <= m && \at(a[j].hi_key, L1) != \null ==> \at(a[j].hi_key, L2) != \null)
      && nonull{L1}(a, m, h, n) ==> nonull{L2}(a, m, h, n);
    lemma reach_grow{L1, L2}: \forall hashitem_T *a, integer m, h, i; tmask(m) && 0 <= h <= 18446744073709551615
      && (\forall integer j; 0 <= j <= m && \at(a[j].hi_key, L1) != \null ==> \at(a[j].hi_key, L2) != \null)
      && reach{L1}(a, m, h, i) ==> reach{L2}(a, m, h, i);
*/
"""

GHOST = r"""
/*@ ghost
  /@ assigns \nothing; ensures \result <==> isused(k); @/
  int isused_c(char *k) { return k != NULL && k != &hash_removed; }

  // p5(m + n) == p5(m) * p5(n) modulo 2^64, by induction on n
  /@ requires 0 <= m && m + n <= SIZE_MAX;
     assigns \nothing;
     ensures p5(m + n) == (size_t)(p5(m) * p5(n)); @/
  void p5_add(size_t m, size_t n) {
    /@ loop invariant 0 <= i <= n && p5(m + i) == (size_t)(p5(m) * p5(i));
       loop assigns i; loop variant n - i; @/
    for (size_t i = 0; i < n; i++) {
      /@ assert p5(m + i + 1) == (size_t)(5 * p5(m + i)); @/
      /@ assert p5(i + 1) == (size_t)(5 * p5(i)); @/
      /@ assert (size_t)(5 * (size_t)(p5(m) * p5(i))) == (size_t)(p5(m) * (size_t)(5 * p5(i))); @/
      /@ assert p5(m + (i + 1)) == (size_t)(p5(m) * p5(i + 1)); @/
      /@ assert (size_t)(i + 1) == i + 1; @/
    }
  }

  size_t vp_rg, vp_rb;
  // From x, g = vp_rg steps of y -> 5*y + 1 reach t (as slots): (4b+1)*x + b with
  // 4b + 1 == 5^g, b = vp_rb. The steps are found one bit at a time (n += P when bit P of
  // the slot value is wrong; A = 5^P has A == 1 + 4P modulo 8P, so P more steps fix it).
  /@ requires tmask(mask) && t <= mask;
     assigns vp_rg, vp_rb;
     ensures vp_rg <= mask && p5(vp_rg) == """ + FA.format(b="vp_rb") + r""";
     ensures (""" + VAL.format(b="vp_rb", x="x") + r""" & mask) == t; @/
  void reach_slot(size_t x, size_t t, size_t mask) {
    size_t n = 0, b = 0, A = 5, P = 1;
    bv_base();
    /@ loop invariant 1 <= P <= 1152921504606846976 && (P & (P - 1)) == 0 && n < P && P <= mask + 1;
       loop invariant p5(n) == """ + FA.format(b="b") + r""";
       loop invariant (""" + VAL.format(b="b", x="x") + r""" & (size_t)(P - 1)) == (t & (size_t)(P - 1));
       loop invariant A == p5(P) && ((size_t)(A - 1) & (size_t)((size_t)(8 * P) - 1)) == (size_t)(4 * P);
       loop assigns n, b, A, P; loop variant 1152921504606846976 - P; @/
    while (P <= mask) {
      bv_pow2_bound(P);
      bv_pow2_le(P, mask);
      bv_step_quarter(A, P);
      if (((4 * b + 1) * x + b & (2 * P - 1)) != (t & (2 * P - 1))) {
        bv_step_val(b, x, A);
        bv_step_bit((4 * b + 1) * x + b, t, A, P);
        bv_step_mult(b, A);
        p5_add(n, P);
        n += P;
        b = A * b + ((A - 1) >> 2);
      }
      bv_square(A, P);
      bv_pow2_double(P);
      p5_add(P, P);
      A = A * A;
      P = 2 * P;
    }
    bv_done(b, x, t, P, mask);
    vp_rg = n; vp_rb = b;
  }

  // strncmp(a, b, n) on a string a and n readable bytes b: what strncmp may read is
  // readable, and a result 0 with no NUL in b[0 .. n-1] means a is exactly b[0 .. n-1]
  /@ requires is_str(a) && \valid_read(b + (0 .. n - 1));
     assigns \nothing;
     ensures \forall integer i; 0 <= i < n ==>
               (\forall integer j; 0 <= j < i ==> a[j] != 0 && a[j] == b[j]) ==> \valid_read(a + i) && \valid_read(b + i);
     ensures ((\forall integer i; 0 <= i < n ==> b[i] != 0)
              && (\forall integer i; 0 <= i < n ==> (\forall integer j; 0 <= j < i ==> a[j] != 0) ==> a[i] == b[i]))
             ==> (\forall integer i; 0 <= i < n ==> a[i] == b[i]) && \valid_read(a + n); @/
  void ncmp_facts(char *a, char *b, size_t n) {
    /@ loop invariant 0 <= i <= n;
       loop invariant ((\forall integer k; 0 <= k < n ==> b[k] != 0)
              && (\forall integer k; 0 <= k < n ==> (\forall integer j; 0 <= j < k ==> a[j] != 0) ==> a[k] == b[k]))
             ==> (\forall integer k; 0 <= k < i ==> a[k] == b[k]) && \valid_read(a + i);
       loop assigns i; loop variant n - i; @/
    for (size_t i = 0; i < n; i++) {}
  }

  // the hash depends only on the bytes
  /@ assigns \nothing;
     ensures (\forall integer i; 0 <= i < n ==> s[i] == t[i]) ==> hl(s, n) == hl(t, n); @/
  void hl_same(char *s, char *t, size_t n) {
    /@ loop invariant 0 <= i <= n;
       loop invariant (\forall integer k; 0 <= k < n ==> s[k] == t[k]) ==> hl(s, i) == hl(t, i);
       loop assigns i; loop variant n - i; @/
    for (size_t i = 0; i < n; i++) {}
  }

  // an item whose key is key[0 .. len-1] has the hash of key[0 .. len-1]
  /@ requires tmask(mask) && i <= mask && \valid_read(a + (0 .. mask)) && isused(a[i].hi_key) && item_ok(a, mask, i);
     requires \forall integer j; 0 <= j < len ==> key[j] != 0;
     assigns \nothing;
     ensures keq(a[i].hi_key, key, len) ==> a[i].hi_hash == hl(key, len); @/
  void key_hash(hashitem_T *a, size_t mask, size_t i, char *key, size_t len) {
    hl_same(a[i].hi_key, key, len);
    /@ assert keq(a[i].hi_key, key, len) ==> \forall integer n; str_len(a[i].hi_key, n) ==> n == len; @/
  }

  /@ requires ht_ok(ht);
     requires \forall integer j; 0 <= j < len ==> key[j] != 0;
     assigns \nothing;
     ensures \forall integer i; 0 <= i <= ht->ht_mask && isused(ht->ht_array[i].hi_key)
               && keq(ht->ht_array[i].hi_key, key, len) ==> ht->ht_array[i].hi_hash == hl(key, len); @/
  void all_keys_hash(hashtab_T *ht, char *key, size_t len) {
    /@ loop invariant 0 <= i <= ht->ht_mask + 1;
       loop invariant \forall integer k; 0 <= k < i && isused(ht->ht_array[k].hi_key)
               && keq(ht->ht_array[k].hi_key, key, len) ==> ht->ht_array[k].hi_hash == hl(key, len);
       loop assigns i; loop variant ht->ht_mask + 1 - i; @/
    for (size_t i = 0; i <= ht->ht_mask; i++) {
      if (isused_c(ht->ht_array[i].hi_key)) key_hash(ht->ht_array, ht->ht_mask, i, key, len);
    }
  }

  // a used item of a well-formed table holds a string
  /@ requires ht_ok(ht) && i <= ht->ht_mask && isused(ht->ht_array[i].hi_key);
     assigns \nothing;
     ensures is_str(ht->ht_array[i].hi_key) && item_ok(ht->ht_array, ht->ht_mask, i); @/
  void item_str(hashtab_T *ht, size_t i) {}

  // probing for key stopped at a never-used item at step N: no item has the key
  /@ requires ht_ok(ht) && \forall integer j; 0 <= j < len ==> key[j] != 0;
     requires \forall integer i; 0 <= i <= ht->ht_mask && isused(ht->ht_array[i].hi_key)
               && keq(ht->ht_array[i].hi_key, key, len) ==> ht->ht_array[i].hi_hash == hash;
     requires \forall integer k; 0 <= k < N ==> !(isused(ht->ht_array[slot(hash, ht->ht_mask, k)].hi_key)
               && keq(ht->ht_array[slot(hash, ht->ht_mask, k)].hi_key, key, len));
     requires nonull(ht->ht_array, ht->ht_mask, hash, N) && ht->ht_array[slot(hash, ht->ht_mask, N)].hi_key == \null;
     assigns \nothing;
     ensures \forall integer i; 0 <= i <= ht->ht_mask && isused(ht->ht_array[i].hi_key)
               ==> !keq(ht->ht_array[i].hi_key, key, len); @/
  void not_found(hashtab_T *ht, char *key, size_t len, size_t hash, size_t N) {}

  // a string of length n has no NUL before n
  /@ requires str_len(s, n);
     assigns \nothing;
     ensures \forall integer i; 0 <= i < n ==> s[i] != 0; @/
  void no_nul(char *s, size_t n) {
    /@ loop invariant 0 <= i <= n && \forall integer k; 0 <= k < i ==> s[k] != 0;
       loop assigns i; loop variant n - i; @/
    for (size_t i = 0; i < n; i++) {
      /@ assert s + i < s + n && \base_addr(s + i) == \base_addr(s); @/
    }
  }

  // no item filled: both counts are 0
  /@ requires \forall integer i; 0 <= i < n ==> a[i].hi_key == \null;
     assigns \nothing;
     ensures nused(a, n) == 0 && nfilled(a, n) == 0; @/
  void counts_zero(hashitem_T *a, size_t n) {
    /@ loop invariant 0 <= i <= n && nused(a, i) == 0 && nfilled(a, i) == 0;
       loop assigns i; loop variant n - i; @/
    for (size_t i = 0; i < n; i++) {}
  }

  // a never-used item exists when fewer than mask + 1 items are non-empty
  /@ requires tmask(mask) && \valid_read(a + (0 .. mask)) && nfilled(a, mask + 1) <= mask;
     assigns \nothing;
     ensures 0 <= \result <= mask && a[\result].hi_key == \null; @/
  size_t find_null(hashitem_T *a, size_t mask) {
    size_t i = 0;
    /@ loop invariant 0 <= i <= mask + 1 && nfilled(a, i) == i;
       loop assigns i; loop variant mask + 1 - i; @/
    while (i <= mask && a[i].hi_key != NULL) {
      i++;
    }
    return i;
  }

  // 0 <= used <= filled <= n
  /@ assigns \nothing;
     ensures 0 <= nused(a, n) <= nfilled(a, n) <= n; @/
  void count_bounds(hashitem_T *a, size_t n) {
    /@ loop invariant 0 <= i <= n && 0 <= nused(a, i) <= nfilled(a, i) <= i;
       loop assigns i; loop variant n - i; @/
    for (size_t i = 0; i < n; i++) {}
  }

  // nused grows with n, and where it stays the same no item is used
  /@ assigns \nothing;
     ensures \forall integer i, j; 0 <= i <= j <= n ==> nused(a, i) <= nused(a, j);
     ensures \forall integer i, j, k; 0 <= i <= k < j <= n && nused(a, i) == nused(a, j) ==> !isused(a[k].hi_key); @/
  void rest_unused(hashitem_T *a, size_t n) {
    /@ loop invariant 0 <= c <= n;
       loop invariant \forall integer i, j; 0 <= i <= j <= c ==> nused(a, i) <= nused(a, j);
       loop invariant \forall integer i, j, k; 0 <= i <= k < j <= c && nused(a, i) == nused(a, j) ==> !isused(a[k].hi_key);
       loop assigns c; loop variant n - c; @/
    for (size_t c = 0; c < n; c++) {}
  }

  // no removed item: used == filled
  /@ requires \forall integer j; 0 <= j < n ==> a[j].hi_key != &hash_removed;
     assigns \nothing;
     ensures nused(a, n) == nfilled(a, n); @/
  void no_removed_counts(hashitem_T *a, size_t n) {
    /@ loop invariant 0 <= i <= n && nused(a, i) == nfilled(a, i);
       loop assigns i; loop variant n - i; @/
    for (size_t i = 0; i < n; i++) {}
  }

  // distinct keys (as strings) are distinct pointers
  /@ requires ht_base(ht);
     assigns \nothing;
     ensures \forall integer i, j; 0 <= i <= ht->ht_mask && 0 <= j <= ht->ht_mask && i != j
               && isused(ht->ht_array[i].hi_key) && isused(ht->ht_array[j].hi_key)
               ==> ht->ht_array[i].hi_key != ht->ht_array[j].hi_key; @/
  void ptrs_distinct(hashtab_T *ht) {}

  // a used item makes the used count positive
  /@ requires s < n && isused(a[s].hi_key);
     assigns \nothing;
     ensures nused(a, n) >= 1; @/
  void used_pos(hashitem_T *a, size_t n, size_t s) {
    /@ loop invariant 0 <= i <= n && nused(a, i) >= 0 && (i > s ==> nused(a, i) >= 1);
       loop assigns i; loop variant n - i; @/
    for (size_t i = 0; i < n; i++) {}
  }

*/
"""


HELPERS = r"""
// Tool-patch helpers (tool_patches.py): field-by-field forms of the memset / memcpy calls,
// proved here by WP and shown byte-identical to the originals in ../equiv/.
/*@ requires \valid(ht);
    assigns ht->ht_mask, ht->ht_used, ht->ht_filled, ht->ht_changed, ht->ht_locked, ht->ht_array,
            ht->ht_smallarray[0 .. HT_INIT_SIZE - 1];
    ensures ht->ht_mask == 0 && ht->ht_used == 0 && ht->ht_filled == 0 && ht->ht_changed == 0
            && ht->ht_locked == 0 && ht->ht_array == \null;
    ensures \forall integer i; 0 <= i < HT_INIT_SIZE ==>
              ht->ht_smallarray[i].hi_hash == 0 && ht->ht_smallarray[i].hi_key == \null; */
static void vp_clear_table(hashtab_T *ht)
{
  ht->ht_mask = 0;
  ht->ht_used = 0;
  ht->ht_filled = 0;
  ht->ht_changed = 0;
  ht->ht_locked = 0;
  ht->ht_array = NULL;
  /*@ loop invariant 0 <= i <= HT_INIT_SIZE;
      loop invariant \forall integer k; 0 <= k < i ==>
        ht->ht_smallarray[k].hi_hash == 0 && ht->ht_smallarray[k].hi_key == \null;
      loop assigns i, ht->ht_smallarray[0 .. HT_INIT_SIZE - 1]; loop variant HT_INIT_SIZE - i; */
  for (int i = 0; i < HT_INIT_SIZE; i++) {
    ht->ht_smallarray[i].hi_hash = 0;
    ht->ht_smallarray[i].hi_key = NULL;
  }
}

/*@ requires \valid(a + (0 .. HT_INIT_SIZE - 1));
    assigns a[0 .. HT_INIT_SIZE - 1];
    ensures \forall integer i; 0 <= i < HT_INIT_SIZE ==> a[i].hi_hash == 0 && a[i].hi_key == \null; */
static void vp_clear_items(hashitem_T *a)
{
  /*@ loop invariant 0 <= i <= HT_INIT_SIZE;
      loop invariant \forall integer k; 0 <= k < i ==> a[k].hi_hash == 0 && a[k].hi_key == \null;
      loop assigns i, a[0 .. HT_INIT_SIZE - 1]; loop variant HT_INIT_SIZE - i; */
  for (int i = 0; i < HT_INIT_SIZE; i++) {
    a[i].hi_hash = 0;
    a[i].hi_key = NULL;
  }
}

/*@ requires \valid(d + (0 .. HT_INIT_SIZE - 1)) && \valid_read(s + (0 .. HT_INIT_SIZE - 1));
    requires \separated(d + (0 .. HT_INIT_SIZE - 1), s + (0 .. HT_INIT_SIZE - 1));
    assigns d[0 .. HT_INIT_SIZE - 1];
    ensures \forall integer i; 0 <= i < HT_INIT_SIZE ==>
              d[i].hi_hash == \old(s[i].hi_hash) && d[i].hi_key == \old(s[i].hi_key);
    ensures \result == d; */
static hashitem_T *vp_copy_items(hashitem_T *d, hashitem_T *s)
{
  /*@ loop invariant 0 <= i <= HT_INIT_SIZE;
      loop invariant \forall integer k; 0 <= k < i ==> d[k].hi_hash == \at(s[k].hi_hash, Pre) && d[k].hi_key == \at(s[k].hi_key, Pre);
      loop assigns i, d[0 .. HT_INIT_SIZE - 1]; loop variant HT_INIT_SIZE - i; */
  for (int i = 0; i < HT_INIT_SIZE; i++) {
    d[i] = s[i];
  }
  return d;
}
"""


def contracts(fixed):
    C = {}
    C["hash_init"] = r"""requires \valid(ht);
    assigns ht->ht_mask, ht->ht_used, ht->ht_filled, ht->ht_changed, ht->ht_locked, ht->ht_array,
            ht->ht_smallarray[0 .. HT_INIT_SIZE - 1];
    ensures ht_ok(ht) && ht->ht_array == &ht->ht_smallarray[0] && ht->ht_mask == HT_INIT_SIZE - 1;
    ensures ht->ht_used == 0 && ht->ht_filled == 0 && ht->ht_changed == 0 && ht->ht_locked == 0;"""
    C["hash_clear"] = r"""requires \valid_read(ht) && vp_nfree < 4294967296;
    requires ht->ht_array != &ht->ht_smallarray[0] ==> vp_live > LONG_MIN && ht->ht_array != \null;
    assigns vp_live, vp_nfree, vp_freelog[vp_nfree];
    behavior small:   // the array is the one inside *ht: nothing to free
      assumes ht->ht_array == &ht->ht_smallarray[0];
      ensures vp_nfree == \old(vp_nfree) && vp_live == \old(vp_live);
    behavior allocated:   // exactly one xfree, of the array
      assumes ht->ht_array != &ht->ht_smallarray[0];
      ensures vp_nfree == \old(vp_nfree) + 1 && vp_freelog[\old(vp_nfree)] == \old(ht->ht_array);
      ensures vp_live == \old(vp_live) - 1;
    complete behaviors; disjoint behaviors;"""
    C["hash_lock"] = r"""requires \valid(ht) && ht->ht_locked < INT_MAX;
    assigns ht->ht_locked;
    ensures ht->ht_locked == \old(ht->ht_locked) + 1;"""
    C["hash_debug_results"] = r"""assigns \nothing;"""
    C["_hash_key_removed"] = r"""assigns \nothing;
    ensures \result == &hash_removed;"""
    C["hash_hash"] = r"""requires str_len((char *)key, n) && n < SIZE_MAX;
    assigns \nothing;
    ensures \result == hl((char *)key, n);"""
    C["hash_hash_len"] = r"""requires \valid_read(key + (0 .. len - 1));
    assigns \nothing;
    ensures \result == hl((char *)key, len);"""
    C["hash_find"] = r"""requires ht_ok((hashtab_T *)ht);
    requires str_len((char *)key, n) && n < SIZE_MAX;
    assigns vp_rg, vp_rb;   // ghost only
    ensures \exists integer k; 0 <= k && \result == ht->ht_array + slot(hl((char *)key, n), ht->ht_mask, k)
              && nonull(ht->ht_array, ht->ht_mask, hl((char *)key, n), k);
    ensures isused(\result->hi_key) ==> keq(\result->hi_key, (char *)key, n);
    ensures !isused(\result->hi_key) ==> \forall integer i; 0 <= i <= ht->ht_mask
              && isused(ht->ht_array[i].hi_key) ==> !keq(ht->ht_array[i].hi_key, (char *)key, n);"""
    C["hash_find_len"] = r"""requires ht_ok((hashtab_T *)ht);
    requires \valid_read(key + (0 .. len - 1)) && \forall integer i; 0 <= i < len ==> key[i] != 0;
    assigns vp_rg, vp_rb;   // ghost only
    ensures \exists integer k; 0 <= k && \result == ht->ht_array + slot(hl((char *)key, len), ht->ht_mask, k)
              && nonull(ht->ht_array, ht->ht_mask, hl((char *)key, len), k);
    ensures isused(\result->hi_key) ==> keq(\result->hi_key, (char *)key, len);
    ensures !isused(\result->hi_key) ==> \forall integer i; 0 <= i <= ht->ht_mask
              && isused(ht->ht_array[i].hi_key) ==> !keq(ht->ht_array[i].hi_key, (char *)key, len);"""
    C["hash_lookup"] = r"""requires ht_ok((hashtab_T *)ht);
    requires \valid_read(key + (0 .. key_len - 1)) && \forall integer i; 0 <= i < key_len ==> key[i] != 0;
    requires hash == hl((char *)key, key_len);
    assigns vp_rg, vp_rb;   // ghost only
    // the item probing stops at: every earlier step met a non-empty item
    ensures \exists integer n; 0 <= n && \result == ht->ht_array + slot(hash, ht->ht_mask, n)
              && nonull(ht->ht_array, ht->ht_mask, hash, n);
    // found: the item with this key
    ensures isused(\result->hi_key) ==> keq(\result->hi_key, (char *)key, key_len);
    // not found: an empty item, and no item has this key
    ensures !isused(\result->hi_key) ==> \forall integer i; 0 <= i <= ht->ht_mask
              && isused(ht->ht_array[i].hi_key) ==> !keq(ht->ht_array[i].hi_key, (char *)key, key_len);"""
    SMALL = "&ht->ht_smallarray[0]"
    # what hash_may_resize does to the allocation state: a new array replacing an
    # allocated one frees it; an allocated new array is one more live allocation
    FREED = f"(\\old(ht->ht_array) != {SMALL} && ht->ht_array != \\old(ht->ht_array))"
    ALLOC = f"""ensures {FREED} ==> vp_nfree == \\old(vp_nfree) + 1 && vp_freelog[\\old(vp_nfree)] == \\old(ht->ht_array);
    ensures !{FREED} ==> vp_nfree == \\old(vp_nfree);
    ensures vp_live == \\old(vp_live) + (ht->ht_array != {SMALL} && ht->ht_array != \\old(ht->ht_array) ? 1 : 0)
                       - ({FREED} ? 1 : 0);
    ensures ht->ht_array != \\old(ht->ht_array) && ht->ht_array != {SMALL} ==>
              \\forall char *q; \\at(\\valid_read(q), Pre) ==> \\base_addr(q) != \\base_addr(ht->ht_array);"""
    SAME = r"""ensures \forall char *k; \forall integer h; has(ht, k, h) <==> \old(has(ht, k, h));"""
    RS_ASSIGNS = (f"ht->ht_array, ht->ht_mask, ht->ht_filled, ht->ht_changed, ht->ht_smallarray[0 .. HT_INIT_SIZE - 1],\n"
                  f"            vp_live, vp_nfree, vp_freelog[vp_nfree], vp_rg, vp_rb")
    MEM = "requires vp_nfree < 4294967296 && LONG_MIN < vp_live < LONG_MAX;"
    UNCHANGED = (r"""ht->ht_array == \old(ht->ht_array) && ht->ht_mask == \old(ht->ht_mask)
              && ht->ht_filled == \old(ht->ht_filled) && ht->ht_changed == \old(ht->ht_changed)""")
    C["hash_may_resize"] = f"""requires ht_base(ht) && ht->ht_filled <= ht->ht_mask + 1;
    requires minitems <= 1152921504606846976;
    requires ht->ht_changed < INT_MAX;   // see findings: ht_changed is a signed int
    {MEM}
    assigns {RS_ASSIGNS};
    exits vp_oom || msz(\\old(ht->ht_used), minitems) > 1152921504606846976;
    ensures ht->ht_used == \\old(ht->ht_used);
    {SAME}
    {ALLOC}
    behavior locked:   // nothing changes
      assumes ht->ht_locked > 0;
      ensures ht_base(ht) && {UNCHANGED};
    behavior kept:     // the table is the right size: nothing changes
      assumes ht->ht_locked <= 0 && keep(ht, minitems);
      ensures ht_ok(ht) && {UNCHANGED};
    behavior resized:  // the items move to a new array of the fitting size, with no removed items
      assumes ht->ht_locked <= 0 && !keep(ht, minitems);
      ensures ht_ok(ht) && fit(ht->ht_mask + 1, msz(\\old(ht->ht_used), minitems));
      ensures ht->ht_filled == ht->ht_used && ht->ht_changed == \\old(ht->ht_changed) + 1;
    complete behaviors; disjoint behaviors;"""
    ITEM = "hi == ht->ht_array + slot(hash, ht->ht_mask, n) && nonull(ht->ht_array, ht->ht_mask, hash, n)"
    NOKEY = lambda k, n: (f"\\forall integer i; 0 <= i <= ht->ht_mask && isused(ht->ht_array[i].hi_key)"
                          f" ==> !keq(ht->ht_array[i].hi_key, {k}, {n})")
    C["hash_add_item"] = f"""requires ht_ok(ht);
    // hi is where hash_lookup stopped for key, which is not in the table
    requires \\exists integer n; 0 <= n && {ITEM};
    requires !isused(hi->hi_key);
    requires isused(key) && str_len(key, len) && len < PTRDIFF_MAX && hash == hl(key, len);
    requires {NOKEY("key", "len")};
    // a locked table is not resized: it must keep a never-used item
    requires ht->ht_locked > 0 && hi->hi_key == \\null ==> ht->ht_filled + 1 <= ht->ht_mask;
    requires ht->ht_changed < INT_MAX - 1;   // see findings
    {MEM}
    assigns hi->hi_key, hi->hi_hash, ht->ht_used, {RS_ASSIGNS};
    exits vp_oom || msz(\\old(ht->ht_used) + 1, 0) > 1152921504606846976;
    ensures ht_ok(ht) && ht->ht_used == \\old(ht->ht_used) + 1;
    ensures \\old(ht->ht_changed) + 1 <= ht->ht_changed <= \\old(ht->ht_changed) + 2;
    ensures \\forall char *k; \\forall integer h; has(ht, k, h) <==> (\\old(has(ht, k, h)) || (k == key && h == hash));
    {ALLOC}"""
    C["hash_remove"] = f"""requires ht_ok(ht);
    requires \\exists integer i; 0 <= i <= ht->ht_mask && hi == ht->ht_array + i;
    requires isused(hi->hi_key);
    requires ht->ht_changed < INT_MAX - 1;   // see findings
    {MEM}
    assigns hi->hi_key, ht->ht_used, {RS_ASSIGNS};
    exits vp_oom || msz(\\old(ht->ht_used) - 1, 0) > 1152921504606846976;
    ensures ht_ok(ht) && ht->ht_used == \\old(ht->ht_used) - 1;
    ensures \\old(ht->ht_changed) + 1 <= ht->ht_changed <= \\old(ht->ht_changed) + 2;
    ensures \\forall char *k; \\forall integer h; has(ht, k, h) <==> (\\old(has(ht, k, h)) && k != \\old(hi->hi_key));
    {ALLOC}"""
    C["hash_unlock"] = f"""requires ht_ok(ht) && ht->ht_locked > INT_MIN;
    requires ht->ht_changed < INT_MAX;   // see findings
    {MEM}
    assigns ht->ht_locked, {RS_ASSIGNS};
    exits vp_oom || msz(\\old(ht->ht_used), 0) > 1152921504606846976;
    ensures ht_ok(ht) && ht->ht_used == \\old(ht->ht_used) && ht->ht_locked == \\old(ht->ht_locked) - 1;
    ensures \\old(ht->ht_changed) <= ht->ht_changed <= \\old(ht->ht_changed) + 1;
    {SAME}
    {ALLOC}"""
    C["hash_add"] = f"""requires ht_ok(ht);
    requires isused(key) && str_len(key, n) && n < PTRDIFF_MAX;
    // a locked table is not resized: it must keep a never-used item after an add
    requires ht->ht_locked > 0 ==> ht->ht_filled + 1 <= ht->ht_mask;
    requires ht->ht_changed < INT_MAX - 1;   // see findings
    {MEM}
    assigns ht->ht_array[0 .. ht->ht_mask], ht->ht_used, {RS_ASSIGNS};
    exits vp_oom || msz(\\old(ht->ht_used) + 1, 0) > 1152921504606846976;
    behavior duplicate:   // an item with this key exists: an internal error, and FAIL
      assumes \\exists integer i; 0 <= i <= ht->ht_mask && isused(ht->ht_array[i].hi_key)
                && keq(ht->ht_array[i].hi_key, key, n);
      ensures \\result == FAIL && ht_ok(ht) && ht->ht_used == \\old(ht->ht_used) && {UNCHANGED};
      {SAME}
      ensures vp_nfree == \\old(vp_nfree) && vp_live == \\old(vp_live);
    behavior added:
      assumes {NOKEY("key", "n")};
      ensures \\result == OK && ht_ok(ht) && ht->ht_used == \\old(ht->ht_used) + 1;
      ensures \\old(ht->ht_changed) + 1 <= ht->ht_changed <= \\old(ht->ht_changed) + 2;
      ensures \\forall char *k; \\forall integer h; has(ht, k, h) <==> (\\old(has(ht, k, h)) || (k == key && h == hl(key, n)));
      {ALLOC.replace(chr(10) + "    ", chr(10) + "      ")}
    complete behaviors; disjoint behaviors;"""
    C["hash_clear_all"] = f"""requires ht_ok(ht);
    requires vp_nfree + ht->ht_used < 4294967295 && vp_live > LONG_MIN + ht->ht_used + 1;
    // each key is `off` bytes into an allocated block
    requires \\forall integer i; 0 <= i <= ht->ht_mask && isused(ht->ht_array[i].hi_key)
               ==> \\valid_read(ht->ht_array[i].hi_key - off);
    assigns vp_live, vp_nfree, vp_freelog[vp_nfree .. vp_nfree + ht->ht_used];
    // the keys are freed in array order, then the array if it was allocated
    ensures \\forall integer i; 0 <= i <= \\old(ht->ht_mask) && \\old(isused(ht->ht_array[i].hi_key))
              ==> vp_freelog[\\old(vp_nfree + nused(ht->ht_array, i))] == \\old(ht->ht_array[i].hi_key - off);
    ensures \\old(ht->ht_array) != {SMALL} ==> vp_freelog[\\old(vp_nfree + ht->ht_used)] == \\old(ht->ht_array);
    ensures vp_nfree == \\old(vp_nfree + ht->ht_used) + (\\old(ht->ht_array) != {SMALL} ? 1 : 0);
    ensures vp_live == \\old(vp_live - ht->ht_used) - (\\old(ht->ht_array) != {SMALL} ? 1 : 0);"""
    return C


def annotations(fixed):
    A = {}
    M = "ht->ht_mask"
    AR = "ht->ht_array"
    NOMATCH = (lambda k: f"!(isused({AR}[slot(hash, {M}, {k})].hi_key) && "
               f"keq({AR}[slot(hash, {M}, {k})].hi_key, (char *)key, key_len))")
    A["hash_hash"] = [
        ("after", "hash_T hash_hash(const char *key)", "ghost (size_t n)"),
        ("before", "  while ((uint8_t)*p != NUL) {", "ghost size_t vp_i = 1; no_nul((char *)key, n);"),
        ("before", "  while ((uint8_t)*p != NUL) {",
         r"""loop invariant 1 <= vp_i <= n && p == key + vp_i && hash == hl((char *)key, vp_i);
      loop assigns hash, p, vp_i; loop variant n - vp_i;"""),
        ("after", "    hash = hash * 101 + (uint8_t)*p++;", "ghost vp_i++;"),
    ]
    A["hash_hash_len"] = [
        ("before", "  while (p < end) {", "ghost size_t vp_i = 1;"),
        ("before", "  while (p < end) {",
         r"""loop invariant 1 <= vp_i <= len && p == key + vp_i && end == key + len && hash == hl((char *)key, vp_i);
      loop assigns hash, p, vp_i; loop variant len - vp_i;"""),
        ("after", "    hash = hash * 101 + (uint8_t)*p++;", "ghost vp_i++;"),
    ]
    A["hash_init"] = [   # "after" entries land in reverse order: the call comes first
        ("after", "  ht->ht_mask = HT_INIT_SIZE - 1;", "assert distinct(ht->ht_array, ht->ht_mask);"),
        ("after", "  ht->ht_mask = HT_INIT_SIZE - 1;", "assert \\forall integer i; 0 <= i <= ht->ht_mask && isused(ht->ht_array[i].hi_key) ==> item_ok(ht->ht_array, ht->ht_mask, i);"),
        ("after", "  ht->ht_mask = HT_INIT_SIZE - 1;", "assert ht->ht_filled == nfilled(ht->ht_array, ht->ht_mask + 1) && ht->ht_filled <= ht->ht_mask;"),
        ("after", "  ht->ht_mask = HT_INIT_SIZE - 1;", "assert ht->ht_used == nused(ht->ht_array, ht->ht_mask + 1);"),
        ("after", "  ht->ht_mask = HT_INIT_SIZE - 1;", "assert (ht->ht_array == &ht->ht_smallarray[0] <==> ht->ht_mask == HT_INIT_SIZE - 1);"),
        ("after", "  ht->ht_mask = HT_INIT_SIZE - 1;", "assert \\valid(ht->ht_array + (0 .. ht->ht_mask));"),
        ("after", "  ht->ht_mask = HT_INIT_SIZE - 1;", "assert tmask(ht->ht_mask);"),
        ("after", "  ht->ht_mask = HT_INIT_SIZE - 1;", "ghost counts_zero(ht->ht_array, HT_INIT_SIZE);"),
    ]
    A["hash_find"] = [
        ("after", "hashitem_T *hash_find(const hashtab_T *const ht, const char *const key)", "ghost (size_t n)"),
        ("inline", "return hash_lookup(ht, key, strlen(key), hash_hash(key));", "ghost no_nul((char *)key, n);"),
        ("after", "hash_hash(key)", "ghost (n)"),
    ]
    A["hash_lookup"] = [
        ("before", "  hash_T idx = hash & ht->ht_mask;",
         "ghost all_keys_hash((hashtab_T *)ht, (char *)key, key_len); bv_mask_le(hash, ht->ht_mask);"),
        ("after", "  hashitem_T *hi = &ht->ht_array[idx];",
         "ghost bv_mask_idem(hash, ht->ht_mask); if (hi->hi_key == NULL) not_found((hashtab_T *)ht, (char *)key, key_len, hash, 0);"),
        ("before", "  hashitem_T *freeitem = NULL;",
         "ghost if (hi->hi_key != HI_KEY_REMOVED) { item_str((hashtab_T *)ht, idx); ncmp_facts(hi->hi_key, (char *)key, key_len); }"),
        ("before", "  for (hash_T perturb = hash;; perturb >>= PERTURB_SHIFT) {",
         f"""ghost size_t vp_t = find_null({AR}, {M});
      size_t vp_n = 0, vp_g = 0, vp_b = 0, vp_oi = 0;
      if (hash == 0) {{ reach_slot(idx, vp_t, {M}); vp_g = vp_rg; vp_b = vp_rb; }}"""),
        ("before", "  for (hash_T perturb = hash;; perturb >>= PERTURB_SHIFT) {",
         f"""loop invariant 0 <= vp_n && idx == pidx(hash, {M}, vp_n) && perturb == pert(hash, vp_n);
      loop invariant hi == {AR} + (idx & {M}) && hi->hi_key != \\null;
      loop invariant nonull({AR}, {M}, hash, vp_n + 1);
      loop invariant \\forall integer k; 0 <= k <= vp_n ==> {NOMATCH("k")};
      loop invariant freeitem == \\null ==> \\forall integer k; 0 <= k <= vp_n ==> {AR}[slot(hash, {M}, k)].hi_key != &hash_removed;
      loop invariant freeitem != \\null ==> \\exists integer k; 0 <= k <= vp_n && freeitem == {AR} + slot(hash, {M}, k)
                       && freeitem->hi_key == &hash_removed && nonull({AR}, {M}, hash, k);
      loop invariant 0 <= vp_t <= {M} && {AR}[vp_t].hi_key == \\null;
      loop invariant perturb != 0 ==> vp_n <= 12 && perturb <= (hash >> (5 * vp_n));
      loop invariant perturb == 0 ==> vp_n + vp_g <= 13 + {M};
      loop invariant perturb == 0 ==> p5(vp_g) == {FA.format(b="vp_b")} && ({VAL.format(b="vp_b", x="idx")} & {M}) == vp_t;
      loop assigns idx, hi, freeitem, perturb, vp_n, vp_g, vp_b, vp_oi, vp_rg, vp_rb;
      loop variant perturb != 0 ? 18446744073709551616 + perturb : vp_g;"""),
        ("inline", "idx = 5 * idx + perturb + 1;",
         f"ghost vp_oi = idx; if (perturb == 0) bv_zero(vp_b, idx, {M});"),
        ("before", "    if ((hi->hi_hash == hash)",
         "ghost if (hi->hi_key != HI_KEY_REMOVED) { item_str((hashtab_T *)ht, idx & ht->ht_mask); ncmp_facts(hi->hi_key, (char *)key, key_len); }"),
        ("before", "    hi = &ht->ht_array[idx & ht->ht_mask];", "ghost bv_mask_le(idx, ht->ht_mask);"),
        ("before", "    if (hi->hi_key == NULL) {",
         f"assert hi == {AR} + slot(hash, {M}, vp_n + 1);"),
        ("before", "    if (hi->hi_key == NULL) {",
         "ghost if (hi->hi_key == NULL) not_found((hashtab_T *)ht, (char *)key, key_len, hash, vp_n + 1);"),
        ("after", "      freeitem = hi;\n    }",
         f"""ghost bv_shr_mono(perturb, hash, 5 * vp_n); bv_shr_zero(hash, 5 * vp_n + 5); vp_n++;
      bv_lsr5(perturb, PERTURB_SHIFT);
      if (perturb == 0) {{ bv_peel(vp_b, vp_oi); vp_b = vp_b - (4 * vp_b + 1) * 14757395258967641293u; vp_g--; }}
      else if ((perturb >> PERTURB_SHIFT) == 0) {{ reach_slot(idx, vp_t, {M}); vp_g = vp_rg; vp_b = vp_rb; }}"""),
    ]
    # a write to one item, at ghost label VpL: the counts change by that item only
    def recount(du, df):
        return f"""ghost {{ size_t vp_j = 0;
      /@ loop invariant 0 <= vp_j <= {M} + 1;
         loop invariant nused({AR}, vp_j) == nused{{VpL}}({AR}, vp_j) + (vp_j > vp_s ? {du} : 0);
         loop invariant nfilled({AR}, vp_j) == nfilled{{VpL}}({AR}, vp_j) + (vp_j > vp_s ? {df} : 0);
         loop assigns vp_j; loop variant {M} + 1 - vp_j; @/
      while (vp_j <= {M}) vp_j++; }}"""
    def settled(extra, mid=()):   # the table before hash_may_resize, from the one write at VpL
        R = "  hash_may_resize(ht, 0);"
        return [("before", R, f"assert \\forall integer j; 0 <= j <= {M} && \\at({AR}[j].hi_key, VpL) != \\null ==> {AR}[j].hi_key != \\null;"),
                ("before", R, f"assert \\forall integer i; 0 <= i <= {M} && i != vp_s ==> {AR}[i].hi_key == \\at({AR}[i].hi_key, VpL) && {AR}[i].hi_hash == \\at({AR}[i].hi_hash, VpL);"),
                ("before", R, f"assert \\forall integer i; 0 <= i <= {M} && i != vp_s && isused({AR}[i].hi_key) ==> item_ok{{VpL}}({AR}, {M}, i);"),
                ("before", R, f"assert \\forall integer i; 0 <= i <= {M} && i != vp_s && isused({AR}[i].hi_key) ==> reach({AR}, {M}, {AR}[i].hi_hash, i);"),
                *mid,
                ("before", R, f"assert \\forall integer i; 0 <= i <= {M} && isused({AR}[i].hi_key) ==> item_ok({AR}, {M}, i);"),
                ("before", R, f"assert distinct({AR}, {M});")] + extra + [("before", R, f"assert ht->ht_used == nused({AR}, {M} + 1);"),
                ("before", R, f"assert ht->ht_filled == nfilled({AR}, {M} + 1);"),
                ("before", R, "assert ht_base(ht);")]
    ADD_S = [("before", "  hash_may_resize(ht, 0);", f"assert {AR}[vp_s].hi_key == key && {AR}[vp_s].hi_hash == hash;"),
             ("before", "  hash_may_resize(ht, 0);", f"assert reach{{Pre}}({AR}, {M}, hash, vp_s);"),
             ("before", "  hash_may_resize(ht, 0);", f"assert \\forall integer j; 0 <= j <= {M} && \\at({AR}[j].hi_key, Pre) != \\null ==> {AR}[j].hi_key != \\null;"),
             ("before", "  hash_may_resize(ht, 0);", f"assert reach({AR}, {M}, hash, vp_s);"),
             ("before", "  hash_may_resize(ht, 0);", f"assert item_ok({AR}, {M}, vp_s);")]
    A["hash_add_item"] = [
        ("after", "void hash_add_item(hashtab_T *ht, hashitem_T *hi, char *key, hash_T hash)", "ghost (size_t len)"),
        ("before", "  ht->ht_used++;", f"ghost count_bounds({AR}, {M} + 1);"),
        ("before", "  hi->hi_key = key;", f"assert \\forall integer i; 0 <= i <= {M} ==> {AR}[i].hi_key == \\at({AR}[i].hi_key, Pre) && {AR}[i].hi_hash == \\at({AR}[i].hi_hash, Pre);"),
        ("before", "  hi->hi_key = key;", f"assert \\forall integer i; 0 <= i <= {M} && isused({AR}[i].hi_key) ==> item_ok({AR}, {M}, i);"),
        ("before", "  hi->hi_key = key;", f"ghost size_t vp_s = hi - {AR};"),
        ("before", "  hi->hi_key = key;", "ghost VpL: ;"),
        ("after", "  hi->hi_hash = hash;", recount("1", "(\\at(hi->hi_key, VpL) == \\null ? 1 : 0)")),
    ] + settled([("before", "  hash_may_resize(ht, 0);", "assert \\forall char *k; \\forall integer h; has(ht, k, h) <==> (\\at(has(ht, k, h), Pre) || (k == key && h == hash));")], ADD_S)
    A["hash_remove"] = [
        ("before", "  ht->ht_used--;", f"ghost count_bounds({AR}, {M} + 1); ptrs_distinct(ht); used_pos({AR}, {M} + 1, hi - {AR});"),
        ("before", "  hi->hi_key = HI_KEY_REMOVED;", f"ghost size_t vp_s = hi - {AR};"),
        ("before", "  hi->hi_key = HI_KEY_REMOVED;", f"assert 0 <= vp_s <= {M} && hi == {AR} + vp_s;"),
        ("before", "  hi->hi_key = HI_KEY_REMOVED;", f"assert ht->ht_used + 1 == nused({AR}, {M} + 1) && ht->ht_filled == nfilled({AR}, {M} + 1);"),
        ("before", "  hi->hi_key = HI_KEY_REMOVED;", "ghost VpL: ;"),
        ("after", "  hi->hi_key = HI_KEY_REMOVED;", recount("-1", "0")),
    ] + settled([("before", "  hash_may_resize(ht, 0);", "assert \\forall char *k; \\forall integer h; has(ht, k, h) <==> (\\at(has(ht, k, h), Pre) && k != \\at(hi->hi_key, Pre));")])
    A["hash_add"] = [
        ("after", "int hash_add(hashtab_T *ht, char *key)", "ghost (size_t n)"),
        ("after", "hash_hash(key)", "ghost (n)"),
        ("before", "  hashitem_T *hi = hash_lookup(", "ghost no_nul(key, n);"),
        ("after", "hash_add_item(ht, hi, key, hash)", "ghost (n)"),
    ]
    A["hash_clear_all"] = [
        ("before", "  size_t todo = ht->ht_used;",
         f"ghost count_bounds({AR}, {M} + 1); rest_unused({AR}, {M} + 1); size_t vp_o = 0;"),
        ("before", "  for (hashitem_T *hi = ht->ht_array; todo > 0; hi++) {",
         f"""loop invariant 0 <= vp_o <= {M} + 1 && hi == {AR} + vp_o;
      loop invariant todo == ht->ht_used - nused({AR}, vp_o);
      loop invariant vp_nfree == \\at(vp_nfree, Pre) + nused({AR}, vp_o) && vp_live == \\at(vp_live, Pre) - nused({AR}, vp_o);
      loop invariant \\forall integer i; 0 <= i < vp_o && isused({AR}[i].hi_key)
                       ==> vp_freelog[\\at(vp_nfree, Pre) + nused({AR}, i)] == {AR}[i].hi_key - off;
      loop assigns hi, todo, vp_o, vp_live, vp_nfree, vp_freelog[\\at(vp_nfree, Pre) .. \\at(vp_nfree, Pre) + ht->ht_used - 1];
      loop variant {M} + 1 - vp_o;"""),
        ("before", "    if (!HASHITEM_EMPTY(hi)) {", "ghost vp_o++;"),
    ]
    return A
