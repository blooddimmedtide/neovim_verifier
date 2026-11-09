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
FIND_KEY_ITEM_LOOP = r"""  /*@ loop invariant src <= p <= src + n;
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
      ensures str_len((char *)str, n - itemlen - 1);
      ensures \forall integer j; 0 <= j < item - str ==> str[j] == \old(str[j]);
      ensures \forall integer j; item - str <= j <= n - itemlen - 1 ==> str[j] == \old(str[j + itemlen + 1]);
    behavior last:    // the last of several items: drop the comma before it and the item
      assumes item[itemlen] != ',' && item > str && *(item - 1) == ',';
      ensures str_len((char *)str, n - itemlen - 1);
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
        ("  while (*p != NUL) {", FIND_KEY_ITEM_LOOP, "before")]),
    "remove_comma_item": (REMOVE_COMMA_ITEM, [("ptrdiff_t itemlen)", GHOST_N, "after")]),
    "append_item": (APPEND_ITEM, [("ptrdiff_t item_len)", GHOST_N, "after")]),
    "prepend_item": (PREPEND_ITEM, [("ptrdiff_t item_len)", GHOST_N, "after")]),
}
