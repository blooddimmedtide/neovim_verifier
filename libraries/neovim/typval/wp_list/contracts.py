"""Specs for the typval list WP proofs, written from each function's documented meaning.

List model: vp_nth(l, i) is an uninterpreted logic function (declared, no axioms), the
item sequence of list l. wf_list(l) says l is a well-formed doubly linked list over that
sequence: lv_first/lv_last are the ends, li_next/li_prev link neighbours, items are valid
and pairwise separated (and separated from l), and a cached lv_idx_item is item lv_idx.
Because vp_nth has no definition, each proof holds for every sequence, so this is the
same as a universally quantified ghost argument.
"""
PRELUDE = r'''
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <limits.h>
#define OK 1
#define FAIL 0
#define FUNC_ATTR_PURE
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_NONNULL_ALL
#define _(x) ((char *)(x))
#define STATIC_ASSERT(...)
/*@ requires c != 0; assigns \nothing; */
void vp_assert(int c);
#define assert(e) vp_assert(e)
typedef enum {
  VAR_UNLOCKED = 0,  ///< Not locked.
  VAR_LOCKED = 1,    ///< User lock, can be unlocked.
  VAR_FIXED = 2,     ///< Locked forever.
} VarLockStatus;
typedef struct listitem_S listitem_T;
// listitem_S: li_tv (the item value) is elided; no function here reads it.
struct listitem_S {
  listitem_T *li_next;  ///< Next item in list.
  listitem_T *li_prev;  ///< Previous item in list.
};
typedef struct listwatch_S listwatch_T;
typedef struct listvar_S list_T;
typedef int LuaRef;
struct listvar_S {
  listitem_T *lv_first;  ///< First item, NULL if none.
  listitem_T *lv_last;  ///< Last item, NULL if none.
  listwatch_T *lv_watch;  ///< First watcher, NULL if none.
  listitem_T *lv_idx_item;  ///< When not NULL item at index "lv_idx".
  list_T *lv_copylist;  ///< Copied list used by deepcopy().
  list_T *lv_used_next;  ///< next list in used lists list.
  list_T *lv_used_prev;  ///< Previous list in used lists list.
  int lv_refcount;  ///< Reference count.
  int lv_len;  ///< Number of items.
  int lv_idx;  ///< Index of a cached item, used for optimising repeated l[idx].
  int lv_copyID;  ///< ID used by deepcopy().
  VarLockStatus lv_lock;  ///< Zero, VAR_LOCKED, VAR_FIXED.

  LuaRef lua_table_ref;
};
extern const char e_list_index_out_of_range_nr[];
//@ ghost int vp_msgs;
/*@ assigns vp_msgs; ensures vp_msgs == \old(vp_msgs) + 1; */
void vp_semsg(void);
#define semsg(...) vp_semsg()

/*@ axiomatic VpListModel {
      logic listitem_T *vp_nth(list_T *l, integer i);
    }
    predicate links(list_T *l) =
      \forall integer i; 0 <= i < l->lv_len ==>
        \valid(vp_nth(l, i)) && \separated(vp_nth(l, i), l) &&
        vp_nth(l, i)->li_next == (i + 1 < l->lv_len ? vp_nth(l, i + 1) : (listitem_T *)\null) &&
        vp_nth(l, i)->li_prev == (i > 0 ? vp_nth(l, i - 1) : (listitem_T *)\null);
    predicate distinct(list_T *l) =
      \forall integer i, j; 0 <= i < l->lv_len && 0 <= j < l->lv_len && i != j ==>
        \separated(vp_nth(l, i), vp_nth(l, j));
    predicate ends(list_T *l) =
      l->lv_len == 0 ? (l->lv_first == \null && l->lv_last == \null)
                     : (l->lv_first == vp_nth(l, 0) && l->lv_last == vp_nth(l, l->lv_len - 1));
    predicate cache_ok(list_T *l) =
      l->lv_idx_item != \null ==> (0 <= l->lv_idx < l->lv_len && l->lv_idx_item == vp_nth(l, l->lv_idx));
    predicate wf_list(list_T *l) =
      \valid(l) && 0 <= l->lv_len && links(l) && distinct(l) && ends(l) && cache_ok(l);
    logic integer uidx(list_T *l, integer n) =
      (n < 0 ? n + (l == \null ? 0 : l->lv_len) : n);
    predicate in_range(list_T *l, integer n) =
      0 <= uidx(l, n) < (l == \null ? 0 : l->lv_len);
*/

/*@ requires l == \null || (\valid_read(l) && l->lv_len >= 0);
    assigns \nothing;
    ensures \result == (l == \null ? 0 : l->lv_len); */
static inline int tv_list_len(const list_T *const l);

/*@ requires l == \null || (\valid_read(l) && l->lv_len >= 0);
    assigns \nothing;
    behavior in: assumes in_range((list_T *)l, n); ensures \result == uidx((list_T *)l, n);
    behavior out: assumes !in_range((list_T *)l, n); ensures \result == -1;
    complete behaviors; disjoint behaviors; */
static inline int tv_list_uidx(const list_T *const l, int n);

/*@ requires l == \null || wf_list(l);
    requires l != \null && l->lv_idx_item != \null ==> l->lv_idx + l->lv_len <= INT_MAX;
    assigns l->lv_idx, l->lv_idx_item;
    ensures l != \null ==> wf_list(l);
    behavior null: assumes l == \null; ensures \result == \null;
    behavior out: assumes l != \null && !in_range(l, n);
      ensures \result == \null && l->lv_idx == \old(l->lv_idx) && l->lv_idx_item == \old(l->lv_idx_item);
    behavior in: assumes l != \null && in_range(l, n);
      ensures \result == vp_nth(l, uidx(l, n));
      ensures l->lv_idx == uidx(l, n) && l->lv_idx_item == \result;
      ensures wf_list(l);
    complete behaviors; disjoint behaviors; */
listitem_T *tv_list_find(list_T *const l, int n);

/*@ requires l == \null || wf_list((list_T *)l);
    assigns \nothing;
    behavior null: assumes l == \null; ensures \result == -1;
    behavior found: assumes l != \null && \exists integer i; 0 <= i < l->lv_len && vp_nth((list_T *)l, i) == item;
      ensures 0 <= \result < l->lv_len && vp_nth((list_T *)l, \result) == item;
    behavior absent: assumes l != \null && !(\exists integer i; 0 <= i < l->lv_len && vp_nth((list_T *)l, i) == item);
      ensures \result == -1;
    complete behaviors; disjoint behaviors; */
int tv_list_idx_of_item(const list_T *const l, const listitem_T *const item);

/*@ requires l == \null || wf_list(l);
    requires l != \null && l->lv_idx_item != \null ==> l->lv_idx + l->lv_len <= INT_MAX;
    requires \valid(idx) && (l == \null || \separated(idx, l));
    requires l != \null ==> \forall integer i; 0 <= i < l->lv_len ==> \separated(idx, vp_nth(l, i));
    assigns *idx, l->lv_idx, l->lv_idx_item;
    ensures l != \null ==> wf_list(l);
    behavior in: assumes in_range(l, *idx);
      ensures \result == vp_nth(l, uidx(l, \old(*idx))) && *idx == \old(*idx);
    behavior neg_clamp: assumes !in_range(l, *idx) && *idx < 0;
      ensures *idx == 0;
      ensures \result == (l != \null && l->lv_len > 0 ? vp_nth(l, 0) : (listitem_T *)\null);
    behavior beyond: assumes !in_range(l, *idx) && *idx >= 0;
      ensures \result == \null && *idx == \old(*idx);
    complete behaviors; disjoint behaviors; */
static listitem_T *tv_list_find_index(list_T *const l, int *const idx);

/*@ requires l == \null || wf_list(l);
    requires l != \null && l->lv_idx_item != \null ==> l->lv_idx + l->lv_len <= INT_MAX;
    requires \valid(n1) && (l == \null || \separated(n1, l));
    requires l != \null ==> \forall integer i; 0 <= i < l->lv_len ==> \separated(n1, vp_nth(l, i));
    assigns *n1, l->lv_idx, l->lv_idx_item, vp_msgs;
    behavior in: assumes in_range(l, *n1);
      ensures \result == vp_nth(l, uidx(l, \old(*n1))) && *n1 == \old(*n1) && vp_msgs == \old(vp_msgs);
    behavior neg_clamp_ok: assumes !in_range(l, *n1) && *n1 < 0 && l != \null && l->lv_len > 0;
      ensures *n1 == 0 && \result == vp_nth(l, 0) && vp_msgs == \old(vp_msgs);
    behavior missing: assumes !in_range(l, *n1) && !(*n1 < 0 && l != \null && l->lv_len > 0);
      ensures \result == \null;
      ensures *n1 == (\old(*n1) < 0 ? 0 : \old(*n1));
      ensures vp_msgs == \old(vp_msgs) + (quiet ? 0 : 1);
    complete behaviors; disjoint behaviors; */
listitem_T *tv_list_check_range_index_one(list_T *const l, int *const n1, const bool quiet);

/*@ requires wf_list(l);
    requires l->lv_idx_item != \null ==> l->lv_idx + l->lv_len <= INT_MAX;
    requires \valid(n1) && \valid(n2) && \separated(n1, n2, l);
    requires \forall integer i; 0 <= i < l->lv_len ==> \separated(n1, vp_nth(l, i)) && \separated(n2, vp_nth(l, i));
    requires *n1 < 0 ==> in_range(l, *n1) && li1 == vp_nth(l, uidx(l, *n1));
    assigns *n1, *n2, l->lv_idx, l->lv_idx_item, vp_msgs;
    behavior n2_missing: assumes *n2 < 0 && !in_range(l, *n2);
      ensures \result == FAIL && *n1 == \old(*n1) && *n2 == \old(*n2);
      ensures vp_msgs == \old(vp_msgs) + (quiet ? 0 : 1);
    behavior checked: assumes !(*n2 < 0 && !in_range(l, *n2));
      ensures *n2 == uidx(l, \old(*n2)) && *n1 == uidx(l, \old(*n1));
      ensures \result == (*n2 >= *n1 ? OK : FAIL);
      ensures vp_msgs == \old(vp_msgs) + (*n2 >= *n1 || quiet ? 0 : 1);
    complete behaviors; disjoint behaviors; */
int tv_list_check_range_index_two(list_T *const l, int *const n1, const listitem_T *const li1,
                                  int *const n2, const bool quiet);

/*@ requires l == \null || wf_list(l);
    requires l != \null ==> INT_MIN + 1 <= l->lv_len - l->lv_idx <= INT_MAX;
    assigns l->lv_first, l->lv_last, l->lv_idx,
            { vp_nth(l, i)->li_next | integer i; 0 <= i < l->lv_len },
            { vp_nth(l, i)->li_prev | integer i; 0 <= i < l->lv_len };
    behavior small: assumes l == \null || l->lv_len <= 1;
      ensures l != \null ==> l->lv_first == \old(l->lv_first) && l->lv_last == \old(l->lv_last) && l->lv_idx == \old(l->lv_idx);
      ensures l != \null ==> \forall integer i; 0 <= i < l->lv_len ==>
        vp_nth(l, i)->li_next == \old(vp_nth(l, i)->li_next) && vp_nth(l, i)->li_prev == \old(vp_nth(l, i)->li_prev);
    behavior big: assumes l != \null && l->lv_len > 1;
      ensures l->lv_first == \old(l->lv_last) && l->lv_last == \old(l->lv_first);
      ensures \forall integer i; 0 <= i < l->lv_len ==>
        vp_nth(l, i)->li_next == \old(vp_nth(l, i)->li_prev) && vp_nth(l, i)->li_prev == \old(vp_nth(l, i)->li_next);
      ensures l->lv_idx == l->lv_len - \old(l->lv_idx) - 1;
    complete behaviors; disjoint behaviors; */
void tv_list_reverse(list_T *const l);
'''

CHECKS = [
    ("src/nvim/vim_defs.h", "# define OK                     1"),
    ("src/nvim/vim_defs.h", "#define FAIL                    0"),
    ("src/nvim/eval/typval_defs.h", "  listitem_T *li_next;  ///< Next item in list."),
    ("src/nvim/eval/typval_defs.h", "  listitem_T *li_prev;  ///< Previous item in list."),
    ("src/nvim/eval/typval_defs.h", "  listitem_T *lv_idx_item;  ///< When not NULL item at index \"lv_idx\"."),
    ("src/nvim/eval/typval_defs.h", "  int lv_len;  ///< Number of items."),
    ("src/nvim/eval/typval_defs.h", "  int lv_idx;  ///< Index of a cached item, used for optimising repeated l[idx]."),
    ("src/nvim/gettext_defs.h", "# define _(x) ((char *)(x))  // NOLINT(bugprone-reserved-identifier)"),
]

LOOPS = {
    "tv_list_check_range_index_two": [
        ("  // Check that n2 isn't before n1.",
         "  /*@ assert l->lv_len == \\at(l->lv_len, Pre); */\n"
         "  /*@ assert links(l); */\n  /*@ assert distinct(l); */\n"
         "  /*@ assert ends(l); */\n  /*@ assert cache_ok(l); */\n"),
    ],
    "tv_list_find": [
        ("  while (n > idx) {",
         "  /*@ loop invariant 0 <= idx < l->lv_len && item == vp_nth(l, idx);\n"
         "      loop invariant idx <= n || idx == \\at(idx, LoopEntry);\n"
         "      loop assigns item, idx; loop variant n - idx; */\n"),
        ("  while (n < idx) {",
         "  /*@ loop invariant n <= idx < l->lv_len && item == vp_nth(l, idx);\n"
         "      loop assigns item, idx; loop variant idx - n; */\n"),
    ],
    "tv_list_idx_of_item": [
        ("for (const listitem_T *li = l_->lv_first;",
         "/*@ loop invariant 0 <= idx <= l->lv_len;\n"
         "    loop invariant li == (idx < l->lv_len ? vp_nth((list_T *)l, idx) : (listitem_T *)\\null);\n"
         "    loop invariant \\forall integer j; 0 <= j < idx ==> vp_nth((list_T *)l, j) != item;\n"
         "    loop assigns li, idx; loop variant l->lv_len - idx; */ "),
    ],
    "tv_list_reverse": [
        ("  for (listitem_T *li = l->lv_first; li != NULL; li = li->li_next) {",
         "  /*@ ghost int k = 0; */\n"
         "  /*@ loop invariant 0 <= k <= l->lv_len;\n"
         "      loop invariant li == (k < l->lv_len ? vp_nth(l, l->lv_len - 1 - k) : (listitem_T *)\\null);\n"
         "      loop invariant l->lv_first == \\at(l->lv_last, Pre) && l->lv_last == \\at(l->lv_first, Pre);\n"
         "      loop invariant l->lv_idx == \\at(l->lv_idx, Pre);\n"
         "      loop invariant \\forall integer i; l->lv_len - k <= i < l->lv_len ==>\n"
         "        vp_nth(l, i)->li_next == \\at(vp_nth(l, i)->li_prev, Pre) && vp_nth(l, i)->li_prev == \\at(vp_nth(l, i)->li_next, Pre);\n"
         "      loop invariant \\forall integer i; 0 <= i < l->lv_len - k ==>\n"
         "        vp_nth(l, i)->li_next == \\at(vp_nth(l, i)->li_next, Pre) && vp_nth(l, i)->li_prev == \\at(vp_nth(l, i)->li_prev, Pre);\n"
         "      loop assigns li, k, tmp, { vp_nth(l, i)->li_next | integer i; 0 <= i < l->lv_len },\n"
         "        { vp_nth(l, i)->li_prev | integer i; 0 <= i < l->lv_len };\n"
         "      loop variant l->lv_len - k; */\n"),
        ("    SWAP(li->li_next, li->li_prev);\n",
         "    /*@ assert li == vp_nth(l, l->lv_len - 1 - k) &&\n"
         "        (\\forall integer i; 0 <= i < l->lv_len && i != l->lv_len - 1 - k ==> \\separated(vp_nth(l, i), li)); */\n"),
        ("  }\n#undef SWAP", "    /*@ ghost k++; */\n"),
    ],
}
