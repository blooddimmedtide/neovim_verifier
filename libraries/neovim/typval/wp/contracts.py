"""Specs for the typval WP proofs. Written from the documented meaning of each function."""
PRELUDE = r'''
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#define OK 1
#define FAIL 0
#define FUNC_ATTR_PURE
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_ALWAYS_INLINE
#define FUNC_ATTR_NONNULL_ALL
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

/*@ assigns vp_msgs;
    behavior ok: assumes 0 <= n1 <= bloblen; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad_quiet: assumes !(0 <= n1 <= bloblen) && quiet; ensures \result == FAIL && vp_msgs == \old(vp_msgs);
    behavior bad_loud: assumes !(0 <= n1 <= bloblen) && !quiet; ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_blob_check_index(int bloblen, varnumber_T n1, bool quiet);

/*@ assigns vp_msgs;
    behavior ok: assumes 0 <= n1 <= n2 < bloblen || (n1 < 0 && 0 <= n2 < bloblen);
      ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad_quiet: assumes !(n1 <= n2 && 0 <= n2 < bloblen) && quiet; ensures \result == FAIL && vp_msgs == \old(vp_msgs);
    behavior bad_loud: assumes !(n1 <= n2 && 0 <= n2 < bloblen) && !quiet; ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
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
    assigns vp_msgs;
    behavior yes: assumes tv->v_type == VAR_NUMBER || tv->v_type == VAR_STRING;
      ensures \result == 1 && vp_msgs == \old(vp_msgs);
    behavior no: assumes !(tv->v_type == VAR_NUMBER || tv->v_type == VAR_STRING);
      ensures \result == 0 && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
bool tv_check_str_or_nr(const typval_T *const tv);

/*@ requires valid_tv((typval_T *)tv);
    assigns vp_msgs;
    behavior yes: assumes tv->v_type \in {VAR_NUMBER, VAR_BOOL, VAR_SPECIAL, VAR_STRING};
      ensures \result == 1 && vp_msgs == \old(vp_msgs);
    behavior no: assumes !(tv->v_type \in {VAR_NUMBER, VAR_BOOL, VAR_SPECIAL, VAR_STRING});
      ensures \result == 0 && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
bool tv_check_num(const typval_T *const tv);

/*@ requires valid_tv((typval_T *)tv);
    assigns vp_msgs;
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
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_STRING}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_STRING}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_string_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_NUMBER}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_NUMBER}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_number_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_FLOAT, VAR_NUMBER}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_FLOAT, VAR_NUMBER}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_float_or_nr_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_BLOB}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_BLOB}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_blob_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_LIST}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_LIST}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_list_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_DICT}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_DICT}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_dict_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_STRING, VAR_NUMBER}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_STRING, VAR_NUMBER}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_string_or_number_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_STRING, VAR_NUMBER}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_STRING, VAR_NUMBER}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_buffer_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_STRING, VAR_NUMBER}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_STRING, VAR_NUMBER}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_lnum_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_STRING, VAR_LIST}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_STRING, VAR_LIST}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_string_or_list_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_STRING, VAR_LIST, VAR_BLOB}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_STRING, VAR_LIST, VAR_BLOB}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_string_or_list_or_blob_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_PARTIAL, VAR_FUNC, VAR_STRING}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_PARTIAL, VAR_FUNC, VAR_STRING}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_string_or_func_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_LIST, VAR_BLOB}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_LIST, VAR_BLOB}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_list_or_blob_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_UNKNOWN, VAR_STRING}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_UNKNOWN, VAR_STRING}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_opt_string_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_UNKNOWN, VAR_NUMBER}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_UNKNOWN, VAR_NUMBER}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_opt_number_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_UNKNOWN, VAR_DICT}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_UNKNOWN, VAR_DICT}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_opt_dict_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type \in {VAR_UNKNOWN, VAR_STRING, VAR_LIST}; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type \in {VAR_UNKNOWN, VAR_STRING, VAR_LIST}); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_opt_string_or_list_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes (args[idx].v_type == VAR_BOOL || (args[idx].v_type == VAR_NUMBER && (args[idx].vval.v_number == 0 || args[idx].vval.v_number == 1))); ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !((args[idx].v_type == VAR_BOOL || (args[idx].v_type == VAR_NUMBER && (args[idx].vval.v_number == 0 || args[idx].vval.v_number == 1)))); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_bool_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes (args[idx].v_type == VAR_UNKNOWN || (args[idx].v_type == VAR_BOOL || (args[idx].v_type == VAR_NUMBER && (args[idx].vval.v_number == 0 || args[idx].vval.v_number == 1)))); ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !((args[idx].v_type == VAR_UNKNOWN || (args[idx].v_type == VAR_BOOL || (args[idx].v_type == VAR_NUMBER && (args[idx].vval.v_number == 0 || args[idx].vval.v_number == 1))))); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_opt_bool_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type == VAR_DICT && args[idx].vval.v_dict != \null; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type == VAR_DICT && args[idx].vval.v_dict != \null); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_nonnull_dict_arg(const typval_T *const args, const int idx);
/*@ requires 0 <= idx <= MAX_FUNC_ARGS && \valid_read(args + idx);
    requires args[idx].v_type == VAR_STRING && args[idx].vval.v_string != \null ==> \valid_read(args[idx].vval.v_string);
    assigns vp_msgs;
    behavior ok: assumes args[idx].v_type == VAR_STRING && args[idx].vval.v_string != \null && args[idx].vval.v_string[0] != 0; ensures \result == OK && vp_msgs == \old(vp_msgs);
    behavior bad: assumes !(args[idx].v_type == VAR_STRING && args[idx].vval.v_string != \null && args[idx].vval.v_string[0] != 0); ensures \result == FAIL && vp_msgs == \old(vp_msgs) + 1;
    complete behaviors; disjoint behaviors; */
int tv_check_for_nonempty_string_arg(const typval_T *const args, const int idx);
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
#define NUL '\000'
'''

CHECKS = [
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
