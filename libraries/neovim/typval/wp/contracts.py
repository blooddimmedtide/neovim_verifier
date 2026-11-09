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
//@ ghost const char *vp_last;  // the message (format) passed to the last emsg/semsg

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
typedef size_t hash_T;
typedef struct {
  hash_T hi_hash;
  char *hi_key;
} hashitem_T;
enum { HT_INIT_SIZE = 16, };
typedef struct {
  hash_T ht_mask;        ///< mask used for hash value
                         ///< (nr of items in array is "ht_mask" + 1)
  size_t ht_used;        ///< number of items used
  size_t ht_filled;      ///< number of items used or removed
  int ht_changed;        ///< incremented when adding or removing an item
  int ht_locked;         ///< counter for hash_lock()
  hashitem_T *ht_array;  ///< points to the array, allocated when it's
                         ///< not "ht_smallarray"
  hashitem_T ht_smallarray[HT_INIT_SIZE];  ///< initial array
} hashtab_T;
// dictvar_S: fields up to dv_hashtab verbatim; the used-list links and watchers that
// follow are elided (no function proved here reads them).
struct dictvar_S {
  VarLockStatus dv_lock;  ///< Whole dictionary lock status.
  ScopeType dv_scope;     ///< Non-zero (#VAR_SCOPE, #VAR_DEF_SCOPE) if
                          ///< dictionary represents a scope (i.e. g:, l: …).
  int dv_refcount;        ///< Reference count.
  int dv_copyID;          ///< ID used when recursivery traversing a value.
  hashtab_T dv_hashtab;   ///< Hashtab containing all items.
};
typedef struct partial_S partial_T;
typedef enum {
  kCallbackNone = 0,
  kCallbackFuncref,
  kCallbackPartial,
  kCallbackLua,
  kCallbackExpr,   ///< Vimscript expression, for "expr" options.
} CallbackType;

typedef struct {
  union {
    char *funcref;
    partial_T *partial;
    LuaRef luaref;
    char *expr;    ///< kCallbackExpr: Vimscript, for "expr" options.
  } data;
  CallbackType type;
} Callback;
typedef double float_T;
typedef enum {
  kBoolVarFalse,         ///< v:false
  kBoolVarTrue,          ///< v:true
} BoolVarValue;
typedef enum {
  kSpecialVarNull,   ///< v:null
} SpecialVarValue;
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
/*@ assigns vp_msgs, vp_last; ensures vp_msgs == \old(vp_msgs) + 1 && vp_last == m; */
void vp_emsg(const char *m);
#define emsg(m) vp_emsg(m)
// abort() must be unreachable: its precondition is false, so WP has to prove no call happens.
/*@ requires \false; assigns \nothing; ensures \false; */
void abort(void);


// semsg: only its occurrence matters here (it shows an error message).
/*@ assigns vp_msgs, vp_last; ensures vp_msgs == \old(vp_msgs) + 1 && vp_last == m; */
void vp_semsg(const char *m);
// Arguments are still evaluated (their overflow checks stay in the proof).
#define semsg(fmt, ...) ((void)(__VA_ARGS__), vp_semsg(fmt))

/*@ predicate valid_blob(blob_T *b) =
      \valid_read(b) && 0 <= b->bv_ga.ga_len &&
      (b->bv_ga.ga_len > 0 ==> \valid_read((uint8_t *)b->bv_ga.ga_data + (0 .. b->bv_ga.ga_len - 1)));
    logic integer blen(blob_T *b) = b == \null ? 0 : b->bv_ga.ga_len;
*/

/*@ requires l == \null || (\valid_read(l) && l->lv_len >= 0);
    assigns \nothing;
    ensures \result == (l == \null ? 0 : l->lv_len); */
static inline int tv_list_len(const list_T *const l);

/*@ requires l == \null || (\valid_read(l) && l->lv_len >= 0);
    assigns \nothing;
    behavior in_range_pos: assumes 0 <= n < (l == \null ? 0 : l->lv_len); ensures \result == n;
    behavior in_range_neg: assumes n < 0 && 0 <= n + (l == \null ? 0 : l->lv_len); ensures \result == n + l->lv_len;
    behavior out: assumes !(0 <= n < (l == \null ? 0 : l->lv_len)) && !(n < 0 && 0 <= n + (l == \null ? 0 : l->lv_len));
      ensures \result == -1;
    complete behaviors; disjoint behaviors; */
static inline int tv_list_uidx(const list_T *const l, int n);

/*@ requires b == \null || \valid_read(b);
    assigns \nothing;
    ensures \result == (b == \null ? 0 : b->bv_ga.ga_len); */
static inline int tv_blob_len(const blob_T *const b);

/*@ requires valid_blob((blob_T *)b) && 0 <= idx < b->bv_ga.ga_len;
    assigns \nothing;
    ensures \result == ((uint8_t *)b->bv_ga.ga_data)[idx]; */
static inline uint8_t tv_blob_get(const blob_T *const b, int idx);

/*@ assigns vp_msgs, vp_last;
    behavior ok: assumes 0 <= n1 <= bloblen; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad_quiet: assumes !(0 <= n1 <= bloblen) && quiet; ensures \result == FAIL && vp_msgs == \old(vp_msgs);
    behavior bad_loud: assumes !(0 <= n1 <= bloblen) && !quiet; ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_blobidx;
    complete behaviors; disjoint behaviors; */
int tv_blob_check_index(int bloblen, varnumber_T n1, bool quiet);

/*@ assigns vp_msgs, vp_last;
    behavior ok: assumes 0 <= n1 <= n2 < bloblen || (n1 < 0 && 0 <= n2 < bloblen);
      ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad_quiet: assumes !(n1 <= n2 && 0 <= n2 < bloblen) && quiet; ensures \result == FAIL && vp_msgs == \old(vp_msgs);
    behavior bad_loud: assumes !(n1 <= n2 && 0 <= n2 < bloblen) && !quiet; ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_blobidx;
    complete behaviors; disjoint behaviors; */
int tv_blob_check_range(int bloblen, varnumber_T n1, varnumber_T n2, bool quiet);

/*@ requires b1 == \null || valid_blob((blob_T *)b1);
    requires b2 == \null || valid_blob((blob_T *)b2);
    assigns \nothing;
    ensures \result == 1 <==>
      (blen((blob_T *)b1) == blen((blob_T *)b2) &&
       \forall integer i; 0 <= i < blen((blob_T *)b1) ==>
         ((uint8_t *)b1->bv_ga.ga_data)[i] == ((uint8_t *)b2->bv_ga.ga_data)[i]);
    ensures \result == 0 || \result == 1; */
bool tv_blob_equal(const blob_T *const b1, const blob_T *const b2);
/*@ requires l == \null || \valid_read(l);
    assigns \nothing;
    ensures \result == (l == \null ? VAR_FIXED : l->lv_lock); */
static inline VarLockStatus tv_list_locked(const list_T *const l);

/*@ predicate valid_tv(typval_T *tv) = \valid_read(tv) && VAR_UNKNOWN <= tv->v_type <= VAR_BLOB; */

/*@ requires valid_tv((typval_T *)tv);
    assigns vp_msgs, vp_last;
    behavior yes: assumes tv->v_type == VAR_NUMBER || tv->v_type == VAR_STRING;
      ensures \result == 1 && vp_msgs == \old(vp_msgs);
    behavior no: assumes !(tv->v_type == VAR_NUMBER || tv->v_type == VAR_STRING);
      ensures \result == 0 && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
bool tv_check_str_or_nr(const typval_T *const tv);

/*@ requires valid_tv((typval_T *)tv);
    assigns vp_msgs, vp_last;
    behavior yes: assumes tv->v_type \in {VAR_NUMBER, VAR_BOOL, VAR_SPECIAL, VAR_STRING};
      ensures \result == 1 && vp_msgs == \old(vp_msgs);
    behavior no: assumes !(tv->v_type \in {VAR_NUMBER, VAR_BOOL, VAR_SPECIAL, VAR_STRING});
      ensures \result == 0 && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
bool tv_check_num(const typval_T *const tv);

/*@ requires valid_tv((typval_T *)tv);
    assigns vp_msgs, vp_last;
    behavior yes: assumes tv->v_type \in {VAR_NUMBER, VAR_BOOL, VAR_SPECIAL, VAR_STRING, VAR_FLOAT};
      ensures \result == 1 && vp_msgs == \old(vp_msgs);
    behavior no: assumes !(tv->v_type \in {VAR_NUMBER, VAR_BOOL, VAR_SPECIAL, VAR_STRING, VAR_FLOAT});
      ensures \result == 0 && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
bool tv_check_str(const typval_T *const tv);

/*@ requires \valid_read(tv);
    requires tv->v_type == VAR_LIST && tv->vval.v_list != \null ==> \valid_read(tv->vval.v_list);
    requires tv->v_type == VAR_DICT && tv->vval.v_dict != \null ==> \valid_read(tv->vval.v_dict);
    assigns \nothing;
    ensures \result == 1 <==>
      (tv->v_lock == VAR_LOCKED
       || (tv->v_type == VAR_LIST && tv->vval.v_list != \null && tv->vval.v_list->lv_lock == VAR_LOCKED)
       || (tv->v_type == VAR_DICT && tv->vval.v_dict != \null && tv->vval.v_dict->dv_lock == VAR_LOCKED));
    ensures \result == 0 || \result == 1; */
bool tv_islocked(const typval_T *const tv);

enum { MAX_FUNC_ARGS = 20, };  ///< Maximum number of function arguments
extern const char e_string_required_for_argument_nr[];
extern const char e_non_empty_string_required_for_argument_nr[];
extern const char e_number_required_for_argument_nr[];
extern const char e_float_or_number_required_for_argument_nr[];
extern const char e_bool_required_for_argument_nr[];
extern const char e_blob_required_for_argument_nr[];
extern const char e_list_required_for_argument_nr[];
extern const char e_dict_required_for_argument_nr[];
extern const char e_non_null_dict_required_for_argument_nr[];
extern const char e_string_or_number_required_for_argument_nr[];
extern const char e_string_or_list_required_for_argument_nr[];
extern const char e_string_list_or_blob_required_for_argument_nr[];
extern const char e_string_or_function_required_for_argument_nr[];
extern const char e_list_or_blob_required_for_argument_nr[];
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_STRING}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_STRING}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_string_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_string_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_NUMBER}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_NUMBER}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_number_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_number_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_FLOAT, VAR_NUMBER}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_FLOAT, VAR_NUMBER}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_float_or_number_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_float_or_nr_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_BLOB}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_BLOB}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_blob_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_blob_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_LIST}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_LIST}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_list_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_list_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_DICT}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_DICT}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_dict_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_dict_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_STRING, VAR_NUMBER}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_STRING, VAR_NUMBER}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_string_or_number_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_string_or_number_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_STRING, VAR_NUMBER}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_STRING, VAR_NUMBER}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_string_or_number_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_buffer_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_STRING, VAR_NUMBER}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_STRING, VAR_NUMBER}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_string_or_number_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_lnum_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_STRING, VAR_LIST}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_STRING, VAR_LIST}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_string_or_list_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_string_or_list_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_STRING, VAR_LIST, VAR_BLOB}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_STRING, VAR_LIST, VAR_BLOB}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_string_list_or_blob_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_string_or_list_or_blob_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_PARTIAL, VAR_FUNC, VAR_STRING}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_PARTIAL, VAR_FUNC, VAR_STRING}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_string_or_function_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_string_or_func_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_LIST, VAR_BLOB}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_LIST, VAR_BLOB}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_list_or_blob_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_list_or_blob_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_UNKNOWN, VAR_STRING}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_UNKNOWN, VAR_STRING}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_string_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_opt_string_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_UNKNOWN, VAR_NUMBER}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_UNKNOWN, VAR_NUMBER}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_number_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_opt_number_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_UNKNOWN, VAR_DICT}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_UNKNOWN, VAR_DICT}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_dict_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_opt_dict_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type \in {VAR_UNKNOWN, VAR_STRING, VAR_LIST}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_UNKNOWN, VAR_STRING, VAR_LIST}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_string_or_list_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_opt_string_or_list_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes (args[idx].v_type == VAR_BOOL || (args[idx].v_type == VAR_NUMBER && (args[idx].vval.v_number == 0 || args[idx].vval.v_number == 1))); ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !((args[idx].v_type == VAR_BOOL || (args[idx].v_type == VAR_NUMBER && (args[idx].vval.v_number == 0 || args[idx].vval.v_number == 1)))); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_bool_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_bool_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes (args[idx].v_type == VAR_UNKNOWN || (args[idx].v_type == VAR_BOOL || (args[idx].v_type == VAR_NUMBER && (args[idx].vval.v_number == 0 || args[idx].vval.v_number == 1)))); ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !((args[idx].v_type == VAR_UNKNOWN || (args[idx].v_type == VAR_BOOL || (args[idx].v_type == VAR_NUMBER && (args[idx].vval.v_number == 0 || args[idx].vval.v_number == 1))))); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (char *)e_bool_required_for_argument_nr;
    complete behaviors; disjoint behaviors; */
int tv_check_for_opt_bool_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type == VAR_DICT && args[idx].vval.v_dict != \null; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type == VAR_DICT && args[idx].vval.v_dict != \null); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (args[idx].v_type != VAR_DICT ? (char *)e_dict_required_for_argument_nr : (char *)e_non_null_dict_required_for_argument_nr);
    complete behaviors; disjoint behaviors; */
int tv_check_for_nonnull_dict_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    requires args[idx].v_type == VAR_STRING && args[idx].vval.v_string != \null ==> \valid_read(args[idx].vval.v_string);
    assigns vp_msgs, vp_last;
    behavior ok: assumes args[idx].v_type == VAR_STRING && args[idx].vval.v_string != \null && args[idx].vval.v_string[0] != 0; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type == VAR_STRING && args[idx].vval.v_string != \null && args[idx].vval.v_string[0] != 0); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && vp_last == (args[idx].v_type != VAR_STRING ? (char *)e_string_required_for_argument_nr : (char *)e_non_empty_string_required_for_argument_nr);
    complete behaviors; disjoint behaviors; */
int tv_check_for_nonempty_string_arg(const typval_T *const args, const int idx);
#define NUL '\000'

enum { NUMBUFLEN = 65, };
extern const char e_val_too_large[];
/*@ requires \valid(buf + (0 .. len - 1)) && len > 0;
    assigns buf[0 .. len - 1]; */
int vp_snprintf(char *buf, size_t len);
#define vim_snprintf(buf, len, ...) vp_snprintf(buf, len)
#define PRId64 "ld"

/*@ requires slen > 0;
    assigns vp_msgs, vp_last;
    behavior ok: assumes n <= INT_MAX / slen;
      ensures \result == OK && vp_msgs == \old(vp_msgs) && n * slen <= INT_MAX;
    behavior too_large: assumes n > INT_MAX / slen;
      ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1 && n * slen > INT_MAX;
    complete behaviors; disjoint behaviors; */
int check_repeat_count(varnumber_T slen, varnumber_T n);

/*@ requires valid_tv((typval_T *)tv);
    assigns vp_msgs, vp_last;
    behavior num: assumes tv->v_type == VAR_NUMBER;
      ensures \result == (double)tv->vval.v_number && vp_msgs == \old(vp_msgs);
    behavior flt: assumes tv->v_type == VAR_FLOAT;
      ensures \result == tv->vval.v_float && vp_msgs == \old(vp_msgs);
    behavior other: assumes tv->v_type != VAR_NUMBER && tv->v_type != VAR_FLOAT;
      ensures \result == 0.0 && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
float_T tv_get_float(const typval_T *const tv);

/*@ requires \valid_read(tv) && VAR_UNKNOWN <= tv->v_type <= VAR_BLOB;
    requires (tv->v_type == VAR_STRING || tv->v_type == VAR_FUNC) && tv->vval.v_string != \null ==> \valid_read(tv->vval.v_string);
    requires tv->v_type == VAR_LIST && tv->vval.v_list != \null ==> \valid_read(tv->vval.v_list);
    requires tv->v_type == VAR_DICT && tv->vval.v_dict != \null ==> \valid_read(tv->vval.v_dict);
    requires tv->v_type == VAR_BLOB && tv->vval.v_blob != \null ==> \valid_read(tv->vval.v_blob);
    assigns \nothing;
    ensures \result == 0 || \result == 1;
    ensures \result == 1 <==>
      ((tv->v_type == VAR_NUMBER && tv->vval.v_number != 0)
    || (tv->v_type == VAR_FLOAT && !(tv->vval.v_float == 0.0))
    || (tv->v_type == VAR_PARTIAL && tv->vval.v_partial != \null)
    || ((tv->v_type == VAR_FUNC || tv->v_type == VAR_STRING) && tv->vval.v_string != \null && tv->vval.v_string[0] != 0)
    || (tv->v_type == VAR_LIST && tv->vval.v_list != \null && tv->vval.v_list->lv_len > 0)
    || (tv->v_type == VAR_DICT && tv->vval.v_dict != \null && tv->vval.v_dict->dv_hashtab.ht_used > 0)
    || (tv->v_type == VAR_BOOL && tv->vval.v_bool == kBoolVarTrue)
    || (tv->v_type == VAR_SPECIAL && tv->vval.v_special != kSpecialVarNull)
    || (tv->v_type == VAR_BLOB && tv->vval.v_blob != \null && tv->vval.v_blob->bv_ga.ga_len > 0)); */
bool tv2bool(const typval_T *const tv);

// ---- strings: predicates and strequal's contract copied from memory/wp (proved there)
/*@ predicate str_len{L}(char *s, integer n) =
      0 <= n && \valid_read(s + (0 .. n)) && s[n] == 0
      && \forall char *q; \base_addr(q) == \base_addr(s) && s <= q < s + n ==> *q != 0;
    predicate is_str{L}(char *s) = \exists integer n; str_len(s, n);
    predicate str_eq{L}(char *a, char *b) = (a == \null && b == \null)
            || (a != \null && b != \null && \exists integer n; str_len((char *)a, n) && str_len((char *)b, n)
                && \forall integer i; 0 <= i < n ==> a[i] == b[i]);
*/
/*@ requires a == \null || is_str((char *)a);
    requires b == \null || is_str((char *)b);
    assigns \nothing;
    ensures \result <==> (a == \null && b == \null)
            || (a != \null && b != \null && \exists integer n; str_len((char *)a, n) && str_len((char *)b, n)
                && \forall integer i; 0 <= i < n ==> a[i] == b[i]); */
bool strequal(const char *a, const char *b);

typedef uint64_t uvarnumber_T;
enum {
  STR2NR_DEC = 0,
  STR2NR_BIN = (1 << 0),  ///< Allow binary numbers.
  STR2NR_OCT = (1 << 1),  ///< Allow octal numbers.
  STR2NR_HEX = (1 << 2),  ///< Allow hexadecimal numbers.
  STR2NR_OOCT = (1 << 3),  ///< Octal with prefix "0o": 0o777
  STR2NR_ALL = STR2NR_BIN | STR2NR_OCT | STR2NR_HEX | STR2NR_OOCT,
};
// vim_str2nr (charset.c, not proved here): the value it leaves in *nptr depends only on
// the string and the old *nptr (uninterpreted). Only this call shape is used.
/*@ logic varnumber_T str2nr_all{L}(char *s, varnumber_T old) reads s[0 ..]; */
/*@ requires is_str((char *)start) && \valid(nptr) && what == STR2NR_ALL && maxlen == 0 && !strict;
    requires prep == \null && len == \null && unptr == \null && overflow == \null;
    assigns *nptr \from ((char *)start)[0 ..], *nptr;
    ensures *nptr == str2nr_all((char *)start, \old(*nptr)); */
void vim_str2nr(const char *const start, int *const prep, int *const len, const int what,
                varnumber_T *const nptr, uvarnumber_T *const unptr, const int maxlen,
                const bool strict, bool *const overflow);
#define FUNC_ATTR_NONNULL_ARG(...)

/*@ predicate num_err_type(integer t) = t \in {VAR_FUNC, VAR_PARTIAL, VAR_LIST, VAR_DICT, VAR_BLOB, VAR_FLOAT, VAR_UNKNOWN};
    logic integer num_value(typval_T *tv) =
      tv->v_type == VAR_NUMBER ? tv->vval.v_number :
      tv->v_type == VAR_STRING ? (tv->vval.v_string == \null ? 0 : str2nr_all(tv->vval.v_string, (varnumber_T)0)) :
      tv->v_type == VAR_BOOL ? (tv->vval.v_bool == kBoolVarTrue ? 1 : 0) : 0;
    predicate num_pre(typval_T *tv) = valid_tv(tv) &&
      (tv->v_type == VAR_STRING && tv->vval.v_string != \null ==> is_str(tv->vval.v_string));
*/
/*@ requires num_pre((typval_T *)tv);
    requires ret_error == \null || (\valid(ret_error) && \separated(ret_error, tv));
    assigns vp_msgs, vp_last, *ret_error;
    behavior good: assumes !num_err_type(tv->v_type);
      ensures \result == num_value((typval_T *)tv) && vp_msgs == \old(vp_msgs);
      ensures ret_error != \null ==> *ret_error == \old(*ret_error);
    behavior bad_ptr: assumes num_err_type(tv->v_type) && ret_error != \null;
      ensures \result == 0 && *ret_error == 1 && vp_msgs == \old(vp_msgs) + 1;
    behavior bad_null: assumes num_err_type(tv->v_type) && ret_error == \null;
      ensures \result == -1 && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
varnumber_T tv_get_number_chk(const typval_T *const tv, bool *const ret_error);

/*@ requires num_pre((typval_T *)tv);
    assigns vp_msgs, vp_last;
    ensures \result == (num_err_type(tv->v_type) ? 0 : num_value((typval_T *)tv));
    ensures vp_msgs == \old(vp_msgs) + (num_err_type(tv->v_type) ? 1 : 0); */
varnumber_T tv_get_number(const typval_T *const tv);

/*@ requires num_pre((typval_T *)tv);
    requires ret_error == \null || (\valid(ret_error) && \separated(ret_error, tv));
    assigns vp_msgs, vp_last, *ret_error;
    behavior good: assumes !num_err_type(tv->v_type);
      ensures \result == num_value((typval_T *)tv) && vp_msgs == \old(vp_msgs);
      ensures ret_error != \null ==> *ret_error == \old(*ret_error);
    behavior bad_ptr: assumes num_err_type(tv->v_type) && ret_error != \null;
      ensures \result == 0 && *ret_error == 1 && vp_msgs == \old(vp_msgs) + 1;
    behavior bad_null: assumes num_err_type(tv->v_type) && ret_error == \null;
      ensures \result == -1 && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
varnumber_T tv_get_bool_chk(const typval_T *const tv, bool *const ret_error);

/*@ requires num_pre((typval_T *)tv);
    assigns vp_msgs, vp_last;
    ensures \result == (num_err_type(tv->v_type) ? -1 : num_value((typval_T *)tv));
    ensures vp_msgs == \old(vp_msgs) + (num_err_type(tv->v_type) ? 1 : 0); */
varnumber_T tv_get_bool(const typval_T *const tv);

/*@ predicate cb_ok(Callback *cb) = \valid_read(cb) && kCallbackNone <= cb->type <= kCallbackExpr
      && (cb->type == kCallbackFuncref ==> (cb->data.funcref == \null || is_str(cb->data.funcref)))
      && (cb->type == kCallbackExpr ==> (cb->data.expr == \null || is_str(cb->data.expr))); */
/*@ requires cb_ok((Callback *)cb1) && cb_ok((Callback *)cb2);
    assigns \nothing;
    ensures \result == 0 || \result == 1;
    ensures \result == 1 <==> cb1->type == cb2->type &&
      (cb1->type == kCallbackFuncref ==> str_eq(cb1->data.funcref, cb2->data.funcref)) &&
      (cb1->type == kCallbackPartial ==> cb1->data.partial == cb2->data.partial) &&
      (cb1->type == kCallbackLua ==> cb1->data.luaref == cb2->data.luaref) &&
      (cb1->type == kCallbackExpr ==> str_eq(cb1->data.expr, cb2->data.expr)); */
bool tv_callback_equal(const Callback *cb1, const Callback *cb2);

// ---- locks
#define TV_TRANSLATE (SIZE_MAX)
#define TV_CSTRING (SIZE_MAX - 1)
extern const char e_value_is_locked[];
extern const char e_value_is_locked_str[];
extern const char e_cannot_change_value[];
extern const char e_cannot_change_value_of_str[];
// assert(): its condition must be proved at each use.
/*@ requires c != 0; assigns \nothing; */
void vp_assert(int c);
#define assert(x) vp_assert((x) != 0)
// strlen: the libc contract used by memory/wp (stubs/vp_string.h)
/*@ requires is_str((char *)s);
    assigns \result \from ((char *)s)[0 ..];
    ensures str_len((char *)s, \result); */
size_t strlen(const char *s);

/*@ predicate lock_ok(integer l) = l \in {VAR_UNLOCKED, VAR_LOCKED, VAR_FIXED};
    predicate name_ok(char *name, size_t name_len) =
      name == \null ||
      ((name_len == TV_TRANSLATE || name_len == TV_CSTRING) ?
         \exists integer n; str_len(name, n) && n <= INT_MAX :
         name_len <= INT_MAX); */
/*@ requires lock_ok(lock) && name_ok((char *)name, name_len);
    assigns vp_msgs, vp_last;
    ensures \result == 0 || \result == 1;
    ensures \result == 1 <==> lock != VAR_UNLOCKED;
    ensures vp_msgs == \old(vp_msgs) + (lock != VAR_UNLOCKED ? 1 : 0);
    ensures lock == VAR_LOCKED ==> vp_last == (name == \null ? (char *)e_value_is_locked : (char *)e_value_is_locked_str);
    ensures lock == VAR_FIXED ==> vp_last == (name == \null ? (char *)e_cannot_change_value : (char *)e_cannot_change_value_of_str); */
bool value_check_lock(VarLockStatus lock, const char *name, size_t name_len);

/*@ logic integer inner_lock(typval_T *tv) =
      tv->v_type == VAR_BLOB && tv->vval.v_blob != \null ? tv->vval.v_blob->bv_lock :
      tv->v_type == VAR_LIST && tv->vval.v_list != \null ? tv->vval.v_list->lv_lock :
      tv->v_type == VAR_DICT && tv->vval.v_dict != \null ? tv->vval.v_dict->dv_lock : VAR_UNLOCKED; */
/*@ requires \valid_read(tv) && lock_ok(tv->v_lock) && name_ok((char *)name, name_len);
    requires tv->v_type == VAR_BLOB && tv->vval.v_blob != \null ==> \valid_read(tv->vval.v_blob) && lock_ok(tv->vval.v_blob->bv_lock);
    requires tv->v_type == VAR_LIST && tv->vval.v_list != \null ==> \valid_read(tv->vval.v_list) && lock_ok(tv->vval.v_list->lv_lock);
    requires tv->v_type == VAR_DICT && tv->vval.v_dict != \null ==> \valid_read(tv->vval.v_dict) && lock_ok(tv->vval.v_dict->dv_lock);
    assigns vp_msgs, vp_last;
    ensures \result == 0 || \result == 1;
    ensures \result == 1 <==> (tv->v_lock != VAR_UNLOCKED || inner_lock((typval_T *)tv) != VAR_UNLOCKED);
    ensures vp_msgs == \old(vp_msgs) + (\result == 1 ? 1 : 0); */
bool tv_check_lock(const typval_T *tv, const char *name, size_t name_len);

// ---- string getters
extern const char *const encode_bool_var_names[2];   // {"false", "true"} in encode.c
extern const char *const encode_special_var_names[1]; // {"null"}
/*@ predicate short_str(char *s) = \exists integer n; str_len(s, n) && n < NUMBUFLEN; */
// snprintf / vim_snprintf of a number into buf: libc contract (writes a string within the bound)
/*@ requires \valid(buf + (0 .. len - 1)) && len == NUMBUFLEN;
    assigns buf[0 .. len - 1];
    ensures is_str(buf); */
int vp_numstr(char *buf, size_t len);
#define snprintf(buf, len, fmt, v) ((void)(v), vp_numstr(buf, len))
#undef vim_snprintf
#define vim_snprintf(buf, len, fmt, ...) ((void)(__VA_ARGS__), vp_numstr(buf, len))
// strcpy of a short string into a NUMBUFLEN buffer
/*@ requires short_str((char *)s) && \valid(d + (0 .. NUMBUFLEN - 1));
    requires \separated(d + (0 .. NUMBUFLEN - 1), (char *)s + (0 .. NUMBUFLEN - 1));
    assigns d[0 .. NUMBUFLEN - 1];
    ensures is_str(d); */
char *vp_strcpy(char *d, const char *s);
#define STRCPY(d, s) vp_strcpy((char *)(d), (char *)(s))
#define PRIdVARNUMBER PRId64

/*@ predicate names_ok = short_str((char *)encode_bool_var_names[0]) && short_str((char *)encode_bool_var_names[1])
      && short_str((char *)encode_special_var_names[0]); */
/*@ requires valid_tv((typval_T *)tv) && \valid(buf + (0 .. NUMBUFLEN - 1)) && names_ok;
    requires tv->v_type == VAR_BOOL ==> 0 <= tv->vval.v_bool <= 1;
    requires tv->v_type == VAR_SPECIAL ==> tv->vval.v_special == kSpecialVarNull;
    requires \separated(buf + (0 .. NUMBUFLEN - 1), (char *)encode_bool_var_names[0] + (0 .. NUMBUFLEN - 1));
    requires \separated(buf + (0 .. NUMBUFLEN - 1), (char *)encode_bool_var_names[1] + (0 .. NUMBUFLEN - 1));
    requires \separated(buf + (0 .. NUMBUFLEN - 1), (char *)encode_special_var_names[0] + (0 .. NUMBUFLEN - 1));
    assigns vp_msgs, vp_last, buf[0 .. NUMBUFLEN - 1];
    behavior str: assumes tv->v_type == VAR_STRING && tv->vval.v_string != \null;
      ensures \result == tv->vval.v_string && vp_msgs == \old(vp_msgs);
    behavior empty: assumes tv->v_type == VAR_STRING && tv->vval.v_string == \null;
      ensures \result != \null && \result != buf && vp_msgs == \old(vp_msgs);
    behavior conv: assumes tv->v_type \in {VAR_NUMBER, VAR_FLOAT, VAR_BOOL, VAR_SPECIAL};
      ensures \result == buf && is_str(buf) && vp_msgs == \old(vp_msgs);
    behavior bad: assumes tv->v_type \in {VAR_PARTIAL, VAR_FUNC, VAR_LIST, VAR_DICT, VAR_BLOB, VAR_UNKNOWN};
      ensures \result == \null && vp_msgs == \old(vp_msgs) + 1 && vp_last == str_errors[tv->v_type];
    complete behaviors; disjoint behaviors; */
const char *tv_get_string_buf_chk(const typval_T *const tv, char *const buf);

/*@ requires valid_tv((typval_T *)tv) && \valid(buf + (0 .. NUMBUFLEN - 1)) && names_ok;
    requires tv->v_type == VAR_BOOL ==> 0 <= tv->vval.v_bool <= 1;
    requires tv->v_type == VAR_SPECIAL ==> tv->vval.v_special == kSpecialVarNull;
    requires \separated(buf + (0 .. NUMBUFLEN - 1), (char *)encode_bool_var_names[0] + (0 .. NUMBUFLEN - 1));
    requires \separated(buf + (0 .. NUMBUFLEN - 1), (char *)encode_bool_var_names[1] + (0 .. NUMBUFLEN - 1));
    requires \separated(buf + (0 .. NUMBUFLEN - 1), (char *)encode_special_var_names[0] + (0 .. NUMBUFLEN - 1));
    assigns vp_msgs, vp_last, buf[0 .. NUMBUFLEN - 1];
    behavior str: assumes tv->v_type == VAR_STRING && tv->vval.v_string != \null;
      ensures \result == tv->vval.v_string && vp_msgs == \old(vp_msgs);
    behavior empty: assumes tv->v_type == VAR_STRING && tv->vval.v_string == \null;
      ensures \result != \null && \result != buf && vp_msgs == \old(vp_msgs);
    behavior conv: assumes tv->v_type \in {VAR_NUMBER, VAR_FLOAT, VAR_BOOL, VAR_SPECIAL};
      ensures \result == buf && is_str(buf) && vp_msgs == \old(vp_msgs);
    behavior bad: assumes tv->v_type \in {VAR_PARTIAL, VAR_FUNC, VAR_LIST, VAR_DICT, VAR_BLOB, VAR_UNKNOWN};
      ensures \result != \null && \result != buf && vp_msgs == \old(vp_msgs) + 1 && vp_last == str_errors[tv->v_type];
    complete behaviors; disjoint behaviors; */
const char *tv_get_string_buf(const typval_T *const tv, char *const buf);
'''

CHECKS = [
    ("src/nvim/memory.h", "#define STRCPY(d, s)        strcpy((char *)(d), (char *)(s))  // NOLINT(runtime/printf)"),
    ("src/nvim/eval/typval_defs.h", "#define PRIdVARNUMBER PRId64"),
    ("src/nvim/eval/typval.h", "#define TV_TRANSLATE (SIZE_MAX)"),
    ("src/nvim/eval/typval.h", "#define TV_CSTRING (SIZE_MAX - 1)"),
    ("src/nvim/charset.h", "  STR2NR_ALL = STR2NR_BIN | STR2NR_OCT | STR2NR_HEX | STR2NR_OOCT,"),
    ("src/nvim/eval/typval_defs.h", "    char *expr;    ///< kCallbackExpr: Vimscript, for \"expr\" options."),
    ("src/nvim/eval/typval_defs.h", "  CallbackType type;"),
    ("src/nvim/types_defs.h", "typedef int LuaRef;"),
    ("src/nvim/vim_defs.h", "  NUMBUFLEN = 65,"),
    ("src/nvim/hashtab_defs.h", "  size_t ht_used;        ///< number of items used"),
    ("src/nvim/hashtab_defs.h", "  hashitem_T ht_smallarray[HT_INIT_SIZE];  ///< initial array"),
    ("src/nvim/eval/typval_defs.h", "  hashtab_T dv_hashtab;   ///< Hashtab containing all items."),
    ("src/nvim/eval/typval_defs.h", "  kBoolVarTrue,          ///< v:true"),
    ("src/nvim/eval/typval_defs.h", "  kSpecialVarNull,   ///< v:null"),
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
    "tv_blob_equal": [("  for (int i = 0; i < b1->bv_ga.ga_len; i++) {",
                       "  /*@ loop invariant 0 <= i <= b1->bv_ga.ga_len;\n"
                       "      loop invariant \\forall integer j; 0 <= j < i ==>\n"
                       "        ((uint8_t *)b1->bv_ga.ga_data)[j] == ((uint8_t *)b2->bv_ga.ga_data)[j];\n"
                       "      loop assigns i; loop variant b1->bv_ga.ga_len - i; */\n")],
}
