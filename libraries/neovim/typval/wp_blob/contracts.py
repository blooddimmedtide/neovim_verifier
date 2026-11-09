"""Specs for the typval WP proofs. Written from the documented meaning of each function."""
PRELUDE = r'''
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <limits.h>
#define OK 1
#define FAIL 0
#define FUNC_ATTR_PURE
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_ALWAYS_INLINE
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_NONNULL_ARG(...)
#define FUNC_ATTR_NONNULL_RET
#define _(x) ((char *)(x))
typedef int64_t varnumber_T;
// garray_T, blobvar_S, listitem_S (value field elided: never read here), listvar_S
typedef struct {
  int ga_len;                       // current number of items used
  int ga_maxlen;                    // maximum number of items possible
  int ga_itemsize;                  // sizeof(item)
  int ga_growsize;                  // number of items to grow each time
  void *ga_data;                    // pointer to the first item
} garray_T;
typedef enum {
  VAR_UNLOCKED = 0,  ///< Not locked.
  VAR_LOCKED = 1,    ///< User lock, can be unlocked.
  VAR_FIXED = 2,     ///< Locked forever.
} VarLockStatus;
typedef struct blobvar_S blob_T;
struct blobvar_S {
  garray_T bv_ga;         ///< Growarray with the data.
  int bv_refcount;        ///< Reference count.
  VarLockStatus bv_lock;  ///< VAR_UNLOCKED, VAR_LOCKED, VAR_FIXED.
};
typedef struct listitem_S listitem_T;
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
extern const char e_blobidx[];
//@ ghost int vp_msgs;

typedef enum {
  VAR_UNKNOWN = 0,  ///< Unknown (unspecified) value.
  VAR_NUMBER,       ///< Number, .v_number is used.
  VAR_STRING,       ///< String, .v_string is used.
  VAR_FUNC,         ///< Function reference, .v_string is used as function name.
  VAR_LIST,         ///< List, .v_list is used.
  VAR_DICT,         ///< Dict, .v_dict is used.
  VAR_FLOAT,        ///< Floating-point value, .v_float is used.
  VAR_BOOL,         ///< true, false
  VAR_SPECIAL,      ///< Special value (null), .v_special is used.
  VAR_PARTIAL,      ///< Partial, .v_partial is used.
  VAR_BLOB,         ///< Blob, .v_blob is used.
} VarType;
typedef enum {
  VAR_NO_SCOPE = 0,  ///< Not a scope dictionary.
  VAR_SCOPE = 1,  ///< Scope dictionary which requires prefix (a:, v:, …).
  VAR_DEF_SCOPE = 2,  ///< Scope dictionary which may be accessed without prefix
                      ///< (l:, g:).
} ScopeType;
typedef struct dictvar_S dict_T;
// dictvar_S: leading fields verbatim; the hashtab, used-list links and watchers that
// follow are elided (no function proved here reads them).
struct dictvar_S {
  VarLockStatus dv_lock;  ///< Whole dictionary lock status.
  ScopeType dv_scope;     ///< Non-zero (#VAR_SCOPE, #VAR_DEF_SCOPE) if
                          ///< dictionary represents a scope (i.e. g:, l: …).
  int dv_refcount;        ///< Reference count.
  int dv_copyID;          ///< ID used when recursivery traversing a value.
};
typedef struct partial_S partial_T;
typedef double float_T;
typedef enum { kBoolVarFalse, kBoolVarTrue } BoolVarValue;
typedef enum { kSpecialVarNull } SpecialVarValue;
typedef struct {
  VarType v_type;               ///< Variable type.
  VarLockStatus v_lock;         ///< Variable lock status.
  union typval_vval_union {
    varnumber_T v_number;       ///< Number, for VAR_NUMBER.
    BoolVarValue v_bool;        ///< Bool value, for VAR_BOOL
    SpecialVarValue v_special;  ///< Special value, for VAR_SPECIAL.
    float_T v_float;            ///< Floating-point number, for VAR_FLOAT.
    char *v_string;             ///< String, for VAR_STRING and VAR_FUNC, can be NULL.
    list_T *v_list;             ///< List for VAR_LIST, can be NULL.
    dict_T *v_dict;             ///< Dict for VAR_DICT, can be NULL.
    partial_T *v_partial;       ///< Closure: function with args.
    blob_T *v_blob;             ///< Blob for VAR_BLOB, can be NULL.
  } vval;                       ///< Actual value.
} typval_T;
#define N_(x) x
#define FUNC_ERROR "E703: Using a Funcref as a Number"
static const char *const num_errors[VAR_BLOB + 1];  // values: messages only, passed to emsg
static const char *const str_errors[VAR_BLOB + 1];
extern const char e_intern2[];
/*@ assigns vp_msgs; ensures vp_msgs == \old(vp_msgs) + 1; */
void vp_emsg(void);
#define emsg(...) vp_emsg()
// abort() must be unreachable: its precondition is false, so WP has to prove no call happens.
/*@ requires \false; assigns \nothing; ensures \false; */
void abort(void);


// semsg: only its occurrence matters here (it shows an error message).
/*@ assigns vp_msgs; ensures vp_msgs == \old(vp_msgs) + 1; */
void vp_semsg(void);
// Arguments are still evaluated (their overflow checks stay in the proof).
#define semsg(fmt, ...) ((void)(__VA_ARGS__), vp_semsg())


// ---- allocation and garray (trusted stubs; see RESULTS.md) ----
//@ ghost long vp_live;
/*@ // Freshness. WP does not model `allocates` (one allocation table for all states), so
    // "differs from every block valid before" cannot be stated soundly. Instead each
    // allocator gets ghost arguments naming live objects the caller relies on; the new
    // block's base differs from each (true of any allocator: a new block overlaps no live one).
    predicate live_or_null{L}(char *a) = a == \null || \valid_read(a);
    predicate avoids(void *r, char *a1, char *a2, char *a3) =
      \base_addr((char *)r) != \base_addr(a1) && \base_addr((char *)r) != \base_addr(a2)
      && \base_addr((char *)r) != \base_addr(a3); */
/*@ // xcalloc (memory.c): zeroed block, never NULL (preserve_exit() on failure). Only
    // called here as xcalloc(1, sizeof(blob_T)), so the contract is stated for that call.
    requires count == 1 && size == sizeof(blob_T) && vp_live < LONG_MAX;
    requires live_or_null(a1) && live_or_null(a2) && live_or_null(a3);
    assigns vp_live;
    ensures \valid((blob_T *)\result) && avoids(\result, a1, a2, a3);
    ensures ((blob_T *)\result)->bv_ga.ga_len == 0 && ((blob_T *)\result)->bv_ga.ga_maxlen == 0
         && ((blob_T *)\result)->bv_ga.ga_itemsize == 0 && ((blob_T *)\result)->bv_ga.ga_growsize == 0
         && ((blob_T *)\result)->bv_ga.ga_data == \null
         && ((blob_T *)\result)->bv_refcount == 0 && ((blob_T *)\result)->bv_lock == VAR_UNLOCKED;
    ensures vp_live == \old(vp_live) + 1; */
void *xcalloc(size_t count, size_t size) /*@ ghost (char *a1, char *a2, char *a3) */;
/*@ requires p != \null ==> vp_live > LONG_MIN;
    assigns vp_live;
    ensures vp_live == \old(vp_live) - (p == \null ? 0 : 1); */
void xfree(void *p);
/*@ // xmemdup (memory.c): new copy of len bytes, never NULL
    requires len > 0 && \valid_read((uint8_t *)data + (0 .. len - 1)) && vp_live < LONG_MAX;
    requires live_or_null(a1) && live_or_null(a2) && live_or_null(a3);
    assigns vp_live;
    ensures \valid((uint8_t *)\result + (0 .. len - 1)) && avoids(\result, a1, a2, a3);
    ensures \base_addr((char *)\result) != \base_addr((char *)data);
    ensures \forall integer i; 0 <= i < len ==> ((uint8_t *)\result)[i] == \old(((uint8_t *)data)[i]);
    ensures vp_live == \old(vp_live) + 1; */
void *xmemdup(const void *data, size_t len) /*@ ghost (char *a1, char *a2, char *a3) */;

/*@ logic integer imax(integer a, integer b) = a >= b ? a : b;
    predicate ga_ok{L}(garray_T *g) =
      \valid(g) && 0 <= g->ga_len <= g->ga_maxlen && g->ga_itemsize == 1
      && \valid((uint8_t *)g->ga_data + (0 .. g->ga_maxlen - 1))
      && \base_addr(g) != \base_addr((char *)g->ga_data);
    predicate blob_ok{L}(blob_T *b) = \valid(b) && ga_ok(&b->bv_ga);
*/
/*@ // ga_init: the contract proved in ../../garray (PR #4)
    requires \valid(gap);
    assigns *gap;
    ensures gap->ga_data == \null && gap->ga_maxlen == 0 && gap->ga_len == 0;
    ensures gap->ga_itemsize == itemsize;
    ensures gap->ga_growsize == (growsize < 1 ? 1 : growsize); */
void ga_init(garray_T *gap, int itemsize, int growsize);
/*@ // ga_grow: implied by the contract proved in ../../garray (itemsize 1, upstream:
    // growth must fit in an int, see garray findings/ga-grow-int-overflow.md), plus the
    // allocator freshness above for a moved block)
    requires ga_ok(gap) && vp_live < LONG_MAX && gap->ga_growsize >= 1;
    requires live_or_null(a1) && live_or_null(a2) && live_or_null(a3);
    requires \base_addr(a1) != \base_addr((char *)gap->ga_data) && \base_addr(a2) != \base_addr((char *)gap->ga_data)
          && \base_addr(a3) != \base_addr((char *)gap->ga_data);
    requires gap->ga_len + imax(imax(n, gap->ga_growsize), gap->ga_len / 2) <= INT_MAX;
    assigns gap->ga_maxlen, gap->ga_data, vp_live,
            ((uint8_t *)\at(gap->ga_data, Post))[0 .. \at(gap->ga_maxlen, Post) - 1];
    ensures ga_ok(gap) && gap->ga_len == \old(gap->ga_len) && gap->ga_growsize == \old(gap->ga_growsize);
    ensures gap->ga_maxlen - gap->ga_len >= n;
    ensures \forall integer i; 0 <= i < \old(gap->ga_maxlen) ==>
              ((uint8_t *)gap->ga_data)[i] == \old(((uint8_t *)gap->ga_data)[i]);
    ensures gap->ga_data == \old(gap->ga_data) || avoids(gap->ga_data, a1, a2, a3);
    ensures vp_live == \old(vp_live) + (\old(gap->ga_data) == \null && gap->ga_data != \null ? 1 : 0); */
void ga_grow(garray_T *gap, int n) /*@ ghost (char *a1, char *a2, char *a3) */;
/*@ // ga_clear: the contract proved in ../../garray (free log reduced to the live count)
    requires \valid(gap) && vp_live > LONG_MIN;
    assigns gap->ga_data, gap->ga_maxlen, gap->ga_len, vp_live;
    ensures gap->ga_data == \null && gap->ga_maxlen == 0 && gap->ga_len == 0;
    ensures vp_live == \old(vp_live) - (\old(gap->ga_data) == \null ? 0 : 1); */
void ga_clear(garray_T *gap);
/*@ // tv_clear (typval.c, NOT proved here: it runs the typval_encode walker). Assumed: it
    // changes only the value fields of *tv and memory reachable from it (freed values),
    // and leaves *tv valid. Callers here overwrite v_type/vval right after.
    requires tv == \null || \valid(tv);
    assigns tv->v_type, tv->v_lock, tv->vval, vp_live; */
void tv_clear(typval_T *const tv);

/*@ predicate valid_blob(blob_T *b) =
      \valid_read(b) && 0 <= b->bv_ga.ga_len &&
      (b->bv_ga.ga_len > 0 ==> \valid_read((uint8_t *)b->bv_ga.ga_data + (0 .. b->bv_ga.ga_len - 1)));
    logic integer blen(blob_T *b) = b == \null ? 0 : b->bv_ga.ga_len;
*/


/*@ requires b == \null || \valid_read(b);
    assigns \nothing;
    ensures \result == (b == \null ? 0 : b->bv_ga.ga_len); */
static inline int tv_blob_len(const blob_T *const b);

/*@ requires valid_blob((blob_T *)b) && 0 <= idx < b->bv_ga.ga_len;
    assigns \nothing;
    ensures \result == ((uint8_t *)b->bv_ga.ga_data)[idx]; */
static inline uint8_t tv_blob_get(const blob_T *const b, int idx);

/*@ requires \valid(blob) && \valid((uint8_t *)blob->bv_ga.ga_data + idx);
    assigns ((uint8_t *)blob->bv_ga.ga_data)[idx];
    ensures ((uint8_t *)blob->bv_ga.ga_data)[idx] == c; */
static inline void tv_blob_set(blob_T *const blob, int idx, uint8_t c);

/*@ requires \valid(tv) && (b == \null || \valid(b)) && \separated(tv, b);
    requires b != \null ==> b->bv_refcount < INT_MAX;
    assigns tv->v_type, tv->vval.v_blob, b->bv_refcount;
    ensures tv->v_type == VAR_BLOB && tv->vval.v_blob == b;
    ensures b != \null ==> b->bv_refcount == \old(b->bv_refcount) + 1; */
static inline void tv_blob_set_ret(typval_T *const tv, blob_T *const b);
/*@ requires vp_live < LONG_MAX;
    requires live_or_null(a1) && live_or_null(a2) && live_or_null(a3);
    assigns vp_live, *\result;   // the new blob's own fields
    ensures blob_ok(\result) && avoids(\result, a1, a2, a3);
    ensures \result->bv_ga.ga_len == 0 && \result->bv_ga.ga_maxlen == 0 && \result->bv_ga.ga_data == \null;
    ensures \result->bv_ga.ga_itemsize == 1 && \result->bv_ga.ga_growsize == 100;
    ensures \result->bv_refcount == 0 && \result->bv_lock == VAR_UNLOCKED;
    ensures vp_live == \old(vp_live) + 1; */
blob_T *tv_blob_alloc(void) /*@ ghost (char *a1, char *a2, char *a3) */;

/*@ requires \valid(b) && vp_live > LONG_MIN + 1;
    assigns b->bv_ga.ga_data, b->bv_ga.ga_maxlen, b->bv_ga.ga_len, vp_live;
    ensures vp_live == \old(vp_live) - 1 - (\old(b->bv_ga.ga_data) == \null ? 0 : 1); */
void tv_blob_free(blob_T *const b);

/*@ requires b == \null || (\valid(b) && b->bv_refcount > INT_MIN);
    requires vp_live > LONG_MIN + 1;
    behavior none: assumes b == \null; assigns \nothing;
    behavior keep: assumes b != \null && b->bv_refcount > 1;
      assigns b->bv_refcount;
      ensures b->bv_refcount == \old(b->bv_refcount) - 1;
    behavior free: assumes b != \null && b->bv_refcount <= 1;
      assigns b->bv_refcount, b->bv_ga.ga_data, b->bv_ga.ga_maxlen, b->bv_ga.ga_len, vp_live;
      ensures vp_live == \old(vp_live) - 1 - (\old(b->bv_ga.ga_data) == \null ? 0 : 1);
    complete behaviors; disjoint behaviors; */
void tv_blob_unref(blob_T *const b);

/*@ requires \valid(ret_tv) && vp_live < LONG_MAX;
    requires live_or_null(a1) && live_or_null(a2);
    assigns ret_tv->v_type, ret_tv->vval.v_blob, vp_live, *\result;
    ensures blob_ok(\result) && avoids(\result, (char *)ret_tv, a1, a2);
    ensures ret_tv->v_type == VAR_BLOB && ret_tv->vval.v_blob == \result;
    ensures \result->bv_ga.ga_len == 0 && \result->bv_ga.ga_data == \null && \result->bv_refcount == 1;
    ensures \result->bv_ga.ga_growsize == 100 && \result->bv_lock == VAR_UNLOCKED;
    ensures vp_live == \old(vp_live) + 1; */
blob_T *tv_blob_alloc_ret(typval_T *const ret_tv) /*@ ghost (char *a1, char *a2) */;

/*@ requires \valid(to) && vp_live < LONG_MAX - 1;
    requires from == \null || (valid_blob(from) && \separated(to, from));
    assigns to->v_type, to->v_lock, to->vval.v_blob, vp_live, *\at(to->vval.v_blob, Post);
    ensures to->v_type == VAR_BLOB && to->v_lock == VAR_UNLOCKED;
    behavior null: assumes from == \null; ensures to->vval.v_blob == \null;
    behavior copy: assumes from != \null;
      ensures blob_ok(to->vval.v_blob) && \separated(to->vval.v_blob, from, to);
      ensures to->vval.v_blob->bv_refcount == 1 && to->vval.v_blob->bv_lock == VAR_UNLOCKED;
      ensures to->vval.v_blob->bv_ga.ga_len == from->bv_ga.ga_len;
      ensures \forall integer i; 0 <= i < from->bv_ga.ga_len ==>
        ((uint8_t *)to->vval.v_blob->bv_ga.ga_data)[i] == ((uint8_t *)from->bv_ga.ga_data)[i];
    complete behaviors; disjoint behaviors; */
void tv_blob_copy(blob_T *const from, typval_T *const to);

/*@ predicate rv_blob{L}(typval_T *rettv, integer len) =
      \valid(rettv) && rettv->v_type == VAR_BLOB && rettv->vval.v_blob != \null
      && valid_blob(rettv->vval.v_blob) && len == rettv->vval.v_blob->bv_ga.ga_len
      && \separated(rettv, rettv->vval.v_blob);
    logic integer byte_at{L}(typval_T *rettv, integer i) = ((uint8_t *)rettv->vval.v_blob->bv_ga.ga_data)[i];
*/
/*@ // The byte is taken from rettv's blob (the "blob" argument is not read); every caller
    // passes rettv holding the blob being indexed.
    requires rv_blob(rettv, len);
    assigns rettv->v_type, rettv->v_lock, rettv->vval, vp_live, vp_msgs;
    behavior ok: assumes -len <= idx < len;
      ensures \result == OK && rettv->v_type == VAR_NUMBER && vp_msgs == \old(vp_msgs);
      ensures rettv->vval.v_number == \old(byte_at(rettv, idx < 0 ? idx + len : idx));
    behavior bad: assumes !(-len <= idx < len);
      assigns vp_msgs;
      ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
static int tv_blob_index(const blob_T *blob, int len, varnumber_T idx, typval_T *rettv);

/*@ // slice bounds, as documented for blob[n1 : n2] (inclusive) and slice() (exclusive):
    // negative indexes count from the end, the end is clamped to the last byte.
    logic integer s1(integer len, integer n1) = n1 < 0 ? imax(len + n1, 0) : n1;
    logic integer s2(integer len, integer n2, boolean ex) =
      (n2 < 0 ? len + n2 : (n2 >= len ? len - (ex ? 0 : 1) : n2)) - (ex ? 1 : 0);
    predicate s_empty(integer len, integer n1, integer n2, boolean ex) =
      s1(len, n1) >= len || s2(len, n2, ex) < 0 || s1(len, n1) > s2(len, n2, ex);
*/
/*@ requires rv_blob(rettv, len) && vp_live < LONG_MAX - 1 && 0 <= len < INT_MAX - 100;
    requires exclusive ==> n2 > INT64_MIN;   // upstream: see FINDINGS.md
    assigns rettv->v_type, rettv->v_lock, rettv->vval, vp_live, *\at(rettv->vval.v_blob, Post),
            ((uint8_t *)\at(rettv->vval.v_blob->bv_ga.ga_data, Post))[0 .. \at(rettv->vval.v_blob->bv_ga.ga_maxlen, Post) - 1];
    ensures \result == OK && rettv->v_type == VAR_BLOB;
    behavior empty: assumes s_empty(len, n1, n2, exclusive);
      ensures rettv->vval.v_blob == \null;
    behavior slice: assumes !s_empty(len, n1, n2, exclusive);
      ensures blob_ok(rettv->vval.v_blob) && rettv->vval.v_blob->bv_refcount == 1;
      ensures rettv->vval.v_blob->bv_ga.ga_len == s2(len, n2, exclusive) - s1(len, n1) + 1;
      ensures \forall integer k; 0 <= k < rettv->vval.v_blob->bv_ga.ga_len ==>
        ((uint8_t *)rettv->vval.v_blob->bv_ga.ga_data)[k] == \old(byte_at(rettv, k + s1(len, n1)));
    complete behaviors; disjoint behaviors; */
static int tv_blob_slice(const blob_T *blob, int len, varnumber_T n1, varnumber_T n2,
                         bool exclusive, typval_T *rettv);

/*@ requires rv_blob(rettv, rettv->vval.v_blob->bv_ga.ga_len) && vp_live < LONG_MAX - 1;
    requires rettv->vval.v_blob->bv_ga.ga_len < INT_MAX - 100;
    requires is_range && exclusive ==> n2 > INT64_MIN;
    assigns vp_msgs, rettv->v_type, rettv->v_lock, rettv->vval, vp_live, *\at(rettv->vval.v_blob, Post),
            ((uint8_t *)\at(rettv->vval.v_blob->bv_ga.ga_data, Post))[0 .. \at(rettv->vval.v_blob->bv_ga.ga_maxlen, Post) - 1];
    behavior range: assumes is_range;
      ensures \result == OK && rettv->v_type == VAR_BLOB;
    behavior index: assumes !is_range && -rettv->vval.v_blob->bv_ga.ga_len <= n1 < rettv->vval.v_blob->bv_ga.ga_len;
      ensures \result == OK && rettv->v_type == VAR_NUMBER;
      ensures rettv->vval.v_number == \old(byte_at(rettv, n1 < 0 ? n1 + rettv->vval.v_blob->bv_ga.ga_len : n1));
    behavior bad: assumes !is_range && !(-rettv->vval.v_blob->bv_ga.ga_len <= n1 < rettv->vval.v_blob->bv_ga.ga_len);
      ensures \result == FAIL;
    complete behaviors; disjoint behaviors; */
int tv_blob_slice_or_index(const blob_T *blob, bool is_range, varnumber_T n1, varnumber_T n2,
                           bool exclusive, typval_T *rettv);

/*@ // idx >= 0: both callers test it first (eval.c get_lval_blob: tv_blob_check_index)
    requires blob_ok(blob) && 0 <= idx && vp_live < LONG_MAX;
    requires blob->bv_ga.ga_growsize >= 1;
    requires blob->bv_ga.ga_len + imax(blob->bv_ga.ga_growsize, blob->bv_ga.ga_len / 2) <= INT_MAX;
    assigns blob->bv_ga.ga_len, blob->bv_ga.ga_maxlen, blob->bv_ga.ga_data, vp_live,
            ((uint8_t *)\at(blob->bv_ga.ga_data, Post))[0 .. \at(blob->bv_ga.ga_maxlen, Post) - 1];
    ensures blob_ok(blob);
    behavior set: assumes idx < blob->bv_ga.ga_len;
      ensures blob->bv_ga.ga_len == \old(blob->bv_ga.ga_len) && blob->bv_ga.ga_data == \old(blob->bv_ga.ga_data);
      ensures ((uint8_t *)blob->bv_ga.ga_data)[idx] == byte;
      ensures \forall integer i; 0 <= i < blob->bv_ga.ga_len && i != idx ==>
        ((uint8_t *)blob->bv_ga.ga_data)[i] == \old(((uint8_t *)blob->bv_ga.ga_data)[i]);
    behavior append: assumes idx == blob->bv_ga.ga_len;
      ensures blob->bv_ga.ga_len == \old(blob->bv_ga.ga_len) + 1;
      ensures ((uint8_t *)blob->bv_ga.ga_data)[idx] == byte;
      ensures \forall integer i; 0 <= i < idx ==>
        ((uint8_t *)blob->bv_ga.ga_data)[i] == \old(((uint8_t *)blob->bv_ga.ga_data)[i]);
    behavior beyond: assumes idx > blob->bv_ga.ga_len;
      ensures blob->bv_ga.ga_len == \old(blob->bv_ga.ga_len) && blob->bv_ga.ga_data == \old(blob->bv_ga.ga_data);
      ensures \forall integer i; 0 <= i < blob->bv_ga.ga_len ==>
        ((uint8_t *)blob->bv_ga.ga_data)[i] == \old(((uint8_t *)blob->bv_ga.ga_data)[i]);
    complete behaviors; disjoint behaviors; */
void tv_blob_set_append(blob_T *blob, int idx, uint8_t byte);

/*@ // n1 .. n2 is a checked range of dest (eval.c: tv_blob_check_index/_range; funcs.c:
    // the blob was grown to n * slen first). Indexes are ints at both call sites.
    requires blob_ok(dest) && \valid_read(src) && src->vval.v_blob != \null && valid_blob(src->vval.v_blob);
    requires INT_MIN <= n1 <= INT_MAX && INT_MIN <= n2 <= INT_MAX;
    requires n1 <= n2 ==> 0 <= n1 && n2 < dest->bv_ga.ga_len;
    requires \separated((uint8_t *)dest->bv_ga.ga_data + (0 .. dest->bv_ga.ga_maxlen - 1),
                        (uint8_t *)src->vval.v_blob->bv_ga.ga_data + (0 .. src->vval.v_blob->bv_ga.ga_len - 1),
                        dest, src, src->vval.v_blob);
    assigns ((uint8_t *)dest->bv_ga.ga_data)[n1 .. n2], vp_msgs;
    behavior ok: assumes n2 - n1 + 1 == src->vval.v_blob->bv_ga.ga_len;
      ensures \result == OK && vp_msgs == \old(vp_msgs);
      ensures \forall integer k; 0 <= k <= n2 - n1 ==>
        ((uint8_t *)dest->bv_ga.ga_data)[n1 + k] == ((uint8_t *)src->vval.v_blob->bv_ga.ga_data)[k];
    behavior bad: assumes n2 - n1 + 1 != src->vval.v_blob->bv_ga.ga_len;
      ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_blob_set_range(blob_T *dest, varnumber_T n1, varnumber_T n2, typval_T *src);
'''

CHECKS = [
    ("src/nvim/eval/typval_defs.h", "  int bv_refcount;        ///< Reference count."),
    ("src/nvim/eval/typval_defs.h", "enum { MAX_FUNC_ARGS = 20, };  ///< Maximum number of function arguments"),
    ("src/nvim/ascii_defs.h", "#define NUL             '\\000'"),
    ("src/nvim/eval/typval_defs.h", "  VAR_BLOB,         ///< Blob, .v_blob is used."),
    ("src/nvim/eval/typval_defs.h", "  VarType v_type;               ///< Variable type."),
    ("src/nvim/eval/typval_defs.h", "  VarLockStatus dv_lock;  ///< Whole dictionary lock status."),
    ("src/nvim/eval/typval_defs.h", "    list_T *v_list;             ///< List for VAR_LIST, can be NULL."),
    ("src/nvim/vim_defs.h", "# define OK                     1"),
    ("src/nvim/vim_defs.h", "#define FAIL                    0"),
    ("src/nvim/eval/typval_defs.h", "typedef int64_t varnumber_T;"),
    ("src/nvim/eval/typval_defs.h", "  garray_T bv_ga;         ///< Growarray with the data."),
    ("src/nvim/eval/typval_defs.h", "  listitem_T *li_next;  ///< Next item in list."),
    ("src/nvim/eval/typval_defs.h", "  listitem_T *li_prev;  ///< Previous item in list."),
    ("src/nvim/eval/typval_defs.h", "  int lv_len;  ///< Number of items."),
    ("src/nvim/eval/typval_defs.h", "  int lv_idx;  ///< Index of a cached item, used for optimising repeated l[idx]."),
    ("src/nvim/gettext_defs.h", "# define _(x) ((char *)(x))  // NOLINT(bugprone-reserved-identifier)"),
]

LOOPS = {
    "tv_blob_alloc": [("\n  FUNC_ATTR_NONNULL_RET\n{\n  blob_T *const blob", " /*@ ghost (char *a1, char *a2, char *a3) */"),
                      (";\n  ga_init(&blob->bv_ga, 1, 100);", " /*@ ghost (a1, a2, a3) */")],
    "tv_blob_alloc_ret": [("\n  FUNC_ATTR_NONNULL_ALL FUNC_ATTR_NONNULL_RET\n{\n  blob_T *const b", " /*@ ghost (char *a1, char *a2) */"),
                          (";\n  tv_blob_set_ret(ret_tv, b);", " /*@ ghost ((char *)ret_tv, a1, a2) */")],
    "tv_blob_copy": [(";\n    int len = from->bv_ga.ga_len;", " /*@ ghost ((char *)from, from->bv_ga.ga_len > 0 ? (char *)from->bv_ga.ga_data : (char *)from) */"),
                     (";\n    }\n    to->vval.v_blob->bv_ga.ga_len = len;",
                      " /*@ ghost ((char *)to->vval.v_blob, (char *)to, (char *)from) */")],
    "tv_blob_slice": [(";\n    ga_grow(&new_blob->bv_ga, (int)(n2 - n1 + 1));",
                       " /*@ ghost ((char *)rettv, (char *)rettv->vval.v_blob, (char *)rettv->vval.v_blob->bv_ga.ga_data) */"),
                      (";\n    new_blob->bv_ga.ga_len = (int)(n2 - n1 + 1);",
                       " /*@ ghost ((char *)rettv, (char *)rettv->vval.v_blob, (char *)rettv->vval.v_blob->bv_ga.ga_data) */"),
        ("    for (int i = (int)n1; i <= (int)n2; i++) {",
        "    /*@ loop invariant (int)n1 <= i <= (int)n2 + 1;\n"
        "        loop invariant \\forall integer k; 0 <= k < i - n1 ==>\n"
        "          ((uint8_t *)new_blob->bv_ga.ga_data)[k] == ((uint8_t *)rettv->vval.v_blob->bv_ga.ga_data)[k + n1];\n"
        "        loop assigns i, ((uint8_t *)new_blob->bv_ga.ga_data)[0 .. n2 - n1];\n"
        "        loop variant n2 - i; */\n")],
    "tv_blob_set_append": [(";\n      gap->ga_len++;", " /*@ ghost ((char *)blob, (char *)blob, (char *)blob) */")],
    "tv_blob_set_range": [("  for (int il = (int)n1, ir = 0; il <= (int)n2; il++) {",
        "  /*@ loop invariant n1 <= il <= n2 + 1 || (n1 > n2 && il == n1);\n"
        "      loop invariant ir == il - n1;\n"
        "      loop invariant \\forall integer k; 0 <= k < ir ==>\n"
        "        ((uint8_t *)dest->bv_ga.ga_data)[n1 + k] == ((uint8_t *)src->vval.v_blob->bv_ga.ga_data)[k];\n"
        "      loop assigns il, ir, ((uint8_t *)dest->bv_ga.ga_data)[n1 .. n2];\n"
        "      loop variant n2 - il; */\n")],
}
