"""ACSL contracts for option.c's comma-list helpers, written from their doc comments
(option.c, upstream 7b87ce8):

- find_key_item: "Find a comma-separated item in src that matches the key part of key.
  keylen is the length including ':'. Returns a pointer to the found item in src, or NULL
  if not found. Sets *itemlenp to the length of the found item (up to ',' or NUL)."
- remove_comma_item: "Remove one item of length itemlen at position item from
  comma-separated string str in-place. Handles the comma before or after the item."
- append_item: "Append a comma-separated item to the end of str in-place. Adds a comma
  before the item if str is not empty."
- prepend_item: "Prepend a comma-separated item to the beginning of str in-place. Adds a
  comma after the item if str is not empty."

The reference below is the comma-list meaning of those sentences, not the code.
"""

LOGIC = r"""
/*@ // an item starts at i: the start of the string or right after a ','
    predicate item_start{L}(char *s, integer i) = i == 0 || s[i - 1] == ',';
    // s[i .. i + kl - 1] is the key key[0 .. kl - 1]
    predicate key_at{L}(char *s, integer i, char *key, integer kl) =
      \forall integer j; 0 <= j < kl ==> s[i + j] == key[j];
    // the item at i ends at i + m: the first ',' or NUL from i
    predicate item_end{L}(char *s, integer i, integer m) =
      0 <= m && (s[i + m] == ',' || s[i + m] == 0)
      && \forall integer j; 0 <= j < m ==> s[i + j] != ',' && s[i + j] != 0;

    // a suffix of a string is a string
    lemma str_len_suffix{L}: \forall char *s, integer n, k; str_len(s, n) && 0 <= k <= n ==> str_len(s + k, n - k);
    // a string has one length
    lemma str_len_unique{L}: \forall char *s, integer n, m; str_len(s, n) && str_len(s, m) ==> n == m;
    // the bytes before the NUL, by index
    lemma str_len_nz{L}: \forall char *s, integer n, j; str_len(s, n) && 0 <= j < n ==> s[j] != 0;
    // item_end does not depend on where the pointer starts
    lemma item_end_shift{L}: \forall char *s, integer k, m; item_end(s + k, 0, m) ==> item_end(s, k, m);
    // s[0 .. n] is a string of length n (index form; validity is stated separately)
    predicate str_at{L}(char *s, integer n) = 0 <= n && s[n] == 0 && \forall integer j; 0 <= j < n ==> s[j] != 0;
*/
/*@ ghost
  // strncmp(s, key, kl) == 0 and key has no NUL in its first kl bytes => s starts with key.
  // (Induction on the prefix, done by the loop.)
  /@ requires 0 <= kl;
     requires \forall integer j; 0 <= j < kl ==> key[j] != 0;
     requires \forall integer j; 0 <= j < kl ==> (\forall integer j2; 0 <= j2 < j ==> s[j2] != 0) ==> s[j] == key[j];
     assigns \nothing;
     ensures key_at(s, 0, key, kl); @/
  void key_prefix(char *s, char *key, ptrdiff_t kl) {
    ptrdiff_t j = 0;
    /@ loop invariant 0 <= j <= kl;
       loop invariant \forall integer i; 0 <= i < j ==> s[i] == key[i];
       loop assigns j; loop variant kl - j; @/
    while (j < kl) j++;
  }
*/
"""

FIND_KEY_ITEM = r"""
/*@ requires str_len(src, n) && n < PTRDIFF_MAX;
    requires 0 <= keylen && \valid_read(key + (0 .. keylen - 1));
    requires \forall integer j; 0 <= j < keylen ==> key[j] != 0;   // keylen counts key's own bytes
    requires \valid(itemlenp) && \separated(itemlenp, src + (0 .. n));
    assigns *itemlenp;
    behavior not_found:
      assumes \forall integer i; 0 <= i < n ==> !(item_start(src, i) && key_at(src, i, key, keylen));
      ensures \result == \null;
      assigns \nothing;
    behavior found:
      assumes \exists integer i; 0 <= i < n && item_start(src, i) && key_at(src, i, key, keylen);
      ensures \exists integer i; 0 <= i < n && \result == src + i
              && item_start(src, i) && key_at(src, i, key, keylen)
              && (\forall integer i2; 0 <= i2 < i ==> !(item_start(src, i2) && key_at(src, i2, key, keylen)))
              && item_end(src, i, *itemlenp) && i + *itemlenp <= n;
    complete behaviors; disjoint behaviors;
*/
"""
FIND_KEY_ITEM_LOOP = r"""  /*@ loop invariant \base_addr(p) == \base_addr(src) && src <= p <= src + n;
      loop invariant \forall integer i; 0 <= i < p - src ==> !(item_start(src, i) && key_at(src, i, key, keylen));
      loop assigns p;
      loop variant n - (p - src); */
"""

REMOVE_COMMA_ITEM = r"""
/*@ requires str_len((char *)str, n) && n < PTRDIFF_MAX && \valid((char *)str + (0 .. n));
    requires \base_addr(item) == \base_addr((char *)str) && (char *)str <= item;
    requires 0 <= itemlen && item + itemlen <= (char *)str + n;
    requires item_end(item, 0, itemlen);   // the item is the whole item, up to ',' or NUL
    assigns ((char *)str)[0 .. n];
    behavior inner:   // a ',' follows: drop the item and that comma
      assumes item[itemlen] == ',';
      ensures str_at((char *)str, n - itemlen - 1);
      ensures \forall integer j; 0 <= j < item - str ==> str[j] == \old(str[j]);
      ensures \forall integer j; item - str <= j <= n - itemlen - 1 ==> str[j] == \old(str[j + itemlen + 1]);
    behavior last:    // the last of several items: drop the comma before it and the item
      assumes item[itemlen] != ',' && item > str && *(item - 1) == ',';
      ensures str_at((char *)str, n - itemlen - 1);
      ensures \forall integer j; 0 <= j < item - str - 1 ==> str[j] == \old(str[j]);
      ensures \forall integer j; item - str - 1 <= j <= n - itemlen - 1 ==> str[j] == \old(str[j + itemlen + 1]);
    behavior only:    // the only item: the list ends where the item started
      assumes item[itemlen] != ',' && !(item > str && *(item - 1) == ',');
      ensures \forall integer j; 0 <= j < item - str ==> str[j] == \old(str[j]);
      ensures item[0] == 0;
    complete behaviors; disjoint behaviors;
*/
"""

APPEND_ITEM = r"""
/*@ requires str_len(str, n) && 0 <= item_len && n + 1 + item_len < PTRDIFF_MAX;
    requires \valid(str + (0 .. n + 1 + item_len)) && \valid_read(item + (0 .. item_len - 1));
    requires \separated(item + (0 .. item_len - 1), str + (0 .. n + 1 + item_len));
    assigns str[0 .. n + 1 + item_len];
    behavior empty:
      assumes n == 0;
      ensures \forall integer t; 0 <= t < item_len ==> str[t] == \old(item[t]);
      ensures str[item_len] == 0;
    behavior nonempty:
      assumes n > 0;
      ensures \forall integer j; 0 <= j < n ==> str[j] == \old(str[j]);
      ensures str[n] == ',';
      ensures \forall integer t; 0 <= t < item_len ==> str[n + 1 + t] == \old(item[t]);
      ensures str[n + 1 + item_len] == 0;
    complete behaviors; disjoint behaviors;
*/
"""

PREPEND_ITEM = r"""
/*@ requires str_len(str, n) && 0 <= item_len && n + 1 + item_len < PTRDIFF_MAX;
    requires \valid(str + (0 .. n + item_len + (n > 0 ? 1 : 0))) && \valid_read(item + (0 .. item_len - 1));
    requires \separated(item + (0 .. item_len - 1), str + (0 .. n + item_len + 1));
    assigns str[0 .. n + item_len + (n > 0 ? 1 : 0)];
    ensures \forall integer t; 0 <= t < item_len ==> str[t] == \old(item[t]);
    behavior empty:
      assumes n == 0;
      ensures str[item_len] == 0;
    behavior nonempty:
      assumes n > 0;
      ensures str[item_len] == ',';
      ensures \forall integer j; 0 <= j <= n ==> str[item_len + 1 + j] == \old(str[j]);
    complete behaviors; disjoint behaviors;
*/
"""

GHOST_N = " /*@ ghost (size_t n) */"
CONTRACTS = {
    "find_key_item": (FIND_KEY_ITEM, [
        ("ptrdiff_t *itemlenp)", GHOST_N, "after"),
        ("  while (*p != NUL) {", FIND_KEY_ITEM_LOOP, "before"),
        ("    // Check if this item starts with the same key",
         "    /*@ assert str_len(p, n - (p - src)); */\n", "before"),
        ("      // Find the end of this item", "      /*@ ghost key_prefix(p, key, keylen); */\n"
         "      /*@ assert p - src < n && item_start(src, p - src) && key_at(src, p - src, key, keylen); */\n", "before"),
        ("      return p;", "      /*@ assert item_end(src, p - src, *itemlenp); */\n", "before"),
        ("      *itemlenp = end - p;",
         "      /*@ assert 0 <= end - p && (p - src) + (end - p) <= n && item_end(p, 0, end - p); */\n", "before")]),
    "remove_comma_item": (REMOVE_COMMA_ITEM, [
        ("ptrdiff_t itemlen)", GHOST_N, "after"),
        ("    // Remove item and trailing comma",
         "    /*@ assert str_len(item + itemlen + 1, n - (item - str) - itemlen - 1); */\n", "before"),
        ("    STRMOVE(item, item + itemlen + 1);",
         "\n    /*@ assert \\forall integer j; item - str <= j <= n - itemlen - 1 ==> str[j] == \\at(str[j + itemlen + 1], Pre); */"
         "\n    /*@ assert \\forall integer j; 0 <= j < n - itemlen - 1 ==> str[j] != 0; */", "after"),
        ("    // Last item: remove leading comma and item",
         "    /*@ assert str_len(item + itemlen, n - (item - str) - itemlen); */\n", "before")]),
    "append_item": (APPEND_ITEM, [("ptrdiff_t item_len)", GHOST_N, "after")]),
    "prepend_item": (PREPEND_ITEM, [("ptrdiff_t item_len)", GHOST_N, "after")]),
}

# stropt_concat_with_comma: "Concatenate the original and new values of a string option,
# adding a ',' if needed." For OP_ADDING the result is origval, then ',', then newval
# (a trailing ',' of origval is dropped first for kOptFlagOneComma options, unless it is
# escaped, so the result has no ",,"); otherwise (OP_PREPENDING) newval, ',', origval.
# The ',' is added only for comma-list options when both values are non-empty.
# `upstream` adds the limit under which the int length is right (findings/option-concat-over-2gib.md).
def concat_contract(upstream):
    limit = ("    requires no <= INT_MAX && nn <= INT_MAX;   // upstream keeps lengths in int\n"
             if upstream else "")
    return r"""
/*@ logic integer cc(uint32_t flags, integer no, integer nn) =
      ((flags & kOptFlagComma) != 0 && no > 0 && nn > 0) ? 1 : 0;
    // how much of origval is kept when adding
    logic integer kept_len{L}(char *o, uint32_t flags, integer no, integer nn) =
      (cc(flags, no, nn) == 1 && no > 1 && (flags & kOptFlagOneComma) == kOptFlagOneComma
       && o[no - 1] == ',' && o[no - 2] != '\\') ? no - 1 : no;
*/
/*@ requires str_len((char *)origval, no) && str_len(newval, nn) && no + nn + 2 < PTRDIFF_MAX;
""" + limit + r"""    requires \valid(newval + (0 .. no + nn + 1));
    requires \separated(origval + (0 .. no), newval + (0 .. no + nn + 1));
    assigns newval[0 .. no + nn + 1];
    behavior adding:
      assumes op == OP_ADDING;
      ensures \let k = kept_len((char *)origval, flags, no, nn); \let c = cc(flags, no, nn);
              (\forall integer j; 0 <= j < k ==> newval[j] == origval[j])
              && (c == 1 ==> newval[k] == ',')
              && (\forall integer j; 0 <= j <= nn ==> newval[k + c + j] == \old(newval[j]));
    behavior other:
      assumes op != OP_ADDING;
      ensures \let c = cc(flags, no, nn);
              (\forall integer j; 0 <= j < nn ==> newval[j] == \old(newval[j]))
              && (c == 1 ==> newval[nn] == ',')
              && (\forall integer j; 0 <= j <= no ==> newval[nn + c + j] == origval[j]);
    complete behaviors; disjoint behaviors;
*/
"""

CONCAT_ANCHORS = [("uint32_t flags)", " /*@ ghost (size_t no, size_t nn) */", "after")]
