// Prelude for mark.c functions: types copied from the pinned headers (build.py checks each
// line). buf_T and win_T are cut down to the fields the proved functions use, with the
// upstream field declarations; WP's typed memory model does not depend on struct layout.
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef int32_t linenr_T;
typedef int colnr_T;
typedef int handle_T;
typedef uint64_t Timestamp;
typedef struct AdditionalData AdditionalData;
typedef struct {
  linenr_T lnum;        ///< line number
  colnr_T col;          ///< column number
  colnr_T coladd;
} pos_T;
#define EXTRA_MARKS     ('9' - '0' + 1)
#define NMARKS          ('z' - 'a' + 1)
#define NGLOBALMARKS    (NMARKS + EXTRA_MARKS)
#define JUMPLISTSIZE    100
#define MAXLNUM 0x7fffffff  // enum constant in pos_defs.h
typedef struct {
  linenr_T topline_offset;  ///< Amount of lines from the mark lnum to the top of the window.
  colnr_T skipcol;
} fmarkv_T;
#define INIT_FMARKV { MAXLNUM, 0 }
typedef struct {
  pos_T mark;           ///< Cursor position.
  int fnum;             ///< File number.
  Timestamp timestamp;  ///< Time when this mark was last set.
  fmarkv_T view;  ///< View the mark was created on
  AdditionalData *additional_data;  ///< Additional data from ShaDa file.
} fmark_T;
#define INIT_FMARK { { 0, 0, 0 }, 0, 0, INIT_FMARKV, NULL }
typedef struct {
  fmark_T fmark;       ///< Actual mark.
  char *fname;  ///< File name, used when fnum == 0.
} xfmark_T;
#define INIT_XFMARK { INIT_FMARK, NULL }
typedef struct {
  linenr_T ml_line_count;       // number of lines in the buffer
} memline_T;
typedef struct {
  handle_T handle;              // unique id for the buffer (buffer number)
  memline_T b_ml;               // associated memline (also contains line count
  fmark_T b_namedm[NMARKS];     // current named marks (mark.c)
  fmark_T b_last_cursor;        // cursor position when last unloading this
  fmark_T b_last_insert;        // where Insert mode was left
  fmark_T b_last_change;        // position of last change: '. mark
  fmark_T b_changelist[JUMPLISTSIZE];
  int b_changelistlen;                  // number of active entries
  pos_T b_op_start;
  pos_T b_op_end;
} buf_T;
typedef struct {
  linenr_T w_topline;               // buffer line number of the line at the
  colnr_T w_skipcol;                // starting screen column for the first
  xfmark_T w_jumplist[JUMPLISTSIZE];
  int w_jumplistlen;                    // number of active entries
} win_T;
#define NUL             '\000'
#define ARRAY_SIZE(arr) ((sizeof(arr)/sizeof((arr)[0])) / ((size_t)(!(sizeof(arr) % sizeof((arr)[0])))))
# define _(x) ((char *)(x))  // NOLINT(bugprone-reserved-identifier)
#define FUNC_ATTR_NONNULL_RET
#define FUNC_ATTR_WARN_UNUSED_RESULT
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_NONNULL_ARG(...)
extern const char e_markinval[];
xfmark_T namedfm[NGLOBALMARKS];
// xfree: a ghost log records each pointer freed, in order, so contracts can say exactly
// what a function frees (WP has no model of free itself).
/*@ ghost void *vp_freed[1000]; int vp_nfreed; */
/*@ requires 0 <= vp_nfreed < 1000;
    assigns vp_freed[vp_nfreed], vp_nfreed;
    ensures vp_nfreed == \old(vp_nfreed) + 1 && vp_freed[\old(vp_nfreed)] == ptr; */
void xfree(void *ptr);
