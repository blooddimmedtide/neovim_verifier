// Prelude: the types these helpers use, copied from memfile_defs.h, memline.c and
// memline_defs.h (key lines checked against upstream by build.py), and contracts
// for what they call (xmalloc, xrealloc, xfree, mf_new). Everything in the
// "trusted" section is listed in ../CLAIM.md. No axioms.
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <limits.h>
#include <assert.h>
#include <sys/types.h>
#include "vp_string.h"   // ../../memory/wp/stubs: C-standard strlen contract, no axioms
#define CHECK(c, s) do {} while (0)
#define _(x) ((char *)(x))
#define STACK_INCR      5
#define XFREE_CLEAR(ptr) \
  do { \
    /* Take the address to avoid double evaluation. #1375 */ \
    void **ptr_ = (void **)&(ptr); \
    xfree(*ptr_); \
    /* coverity[dead-store] */ \
    *ptr_ = NULL; \
    (void)(*ptr_); \
  } while (0)
typedef int64_t blocknr_T;
typedef int32_t linenr_T;
typedef int colnr_T;
typedef struct { linenr_T lnum; colnr_T col; colnr_T coladd; } pos_T;
#define FUNC_ATTR_NONNULL_ALL
#define FUNC_ATTR_NONNULL_RET
typedef struct {
  blocknr_T bh_bnum;
  void *bh_data;
  unsigned bh_page_count;
  unsigned bh_flags;
} bhdr_T;
// memfile_T: the map fields (mf_hash, mf_trans) are left out; none of these
// functions touches them.
typedef enum { MF_DIRTY_NO = 0, MF_DIRTY_YES, MF_DIRTY_YES_NOSYNC } mfdirty_T;
typedef struct {
  char *mf_fname; char *mf_ffname; int mf_fd; int mf_flags; bool mf_reopen;
  bhdr_T *mf_free_first;
  blocknr_T mf_blocknr_max; blocknr_T mf_blocknr_min; blocknr_T mf_neg_count;
  blocknr_T mf_infile_count;
  unsigned mf_page_size;
  mfdirty_T mf_dirty;
} memfile_T;
enum { DATA_ID = (('d' << 8) + 'a'), PTR_ID = (('p' << 8) + 't') };
typedef struct {
  blocknr_T pe_bnum; linenr_T pe_line_count; linenr_T pe_old_lnum; int pe_page_count;
} PointerEntry;
typedef struct {
  uint16_t pb_id; uint16_t pb_count; uint16_t pb_count_max; PointerEntry pb_pointer[];
} PointerBlock;
#define PB_COUNT_MAX(mfp) \
  (uint16_t)((mfp->mf_page_size - offsetof(PointerBlock, pb_pointer)) / sizeof(PointerEntry))
typedef struct {
  uint16_t db_id; unsigned db_free; unsigned db_txt_start; unsigned db_txt_end;
  long db_line_count; unsigned db_index[];
} DataBlock;
#define HEADER_SIZE (offsetof(DataBlock, db_index))
// x86_64 layout constants used in the ACSL below (ACSL cannot use offsetof).
_Static_assert(offsetof(DataBlock, db_index) == 24, "HEADER_SIZE");
_Static_assert(offsetof(PointerBlock, pb_pointer) == 8, "pb_pointer offset");
_Static_assert(sizeof(PointerEntry) == 24, "PointerEntry size");
typedef struct {
  blocknr_T ip_bnum; linenr_T ip_low; linenr_T ip_high; int ip_index;
} infoptr_T;
_Static_assert(sizeof(infoptr_T) == 24, "infoptr_T size");
// buf_T / memline_T reduced to the fields these functions use.
#define ML_LINE_DIRTY   0x02
typedef struct { infoptr_T *ml_stack; int ml_stack_top; int ml_stack_size; int ml_flags; } memline_T;
typedef struct {
  memline_T b_ml;
  bool update_need_codepoints;
  size_t deleted_bytes; size_t deleted_bytes2; size_t deleted_codepoints; size_t deleted_codeunits;
} buf_T;
extern buf_T *curbuf;
extern int inhibit_delete_count;

// ---------------------------------------------------------------- trusted
// Ghost log of frees, in order, so contracts can say exactly what is freed.
/*@ ghost size_t vp_nfree; */
/*@ ghost void *vp_freelog[1024]; */

/*@ // memory.c xmalloc: never returns NULL (preserve_exit() on OOM); new memory
    requires n >= 1;
    assigns \result \from n;
    allocates \result;
    ensures \result != \null && \valid((char *)\result + (0 .. n - 1));
*/
void *xmalloc(size_t n);

// Ghost "avoid" object: a live object the caller still uses after the call. A real
// realloc never returns memory overlapping a live object outside the old block, so
// the contract may promise separation from it. (Used instead of a \forall-over-valid-
// pointers freshness clause, which is contradictory in WP since it ignores allocates.)
/*@ ghost buf_T *vp_avoid_buf; */
/*@ // memory.c xrealloc: n bytes, first bytes kept, never NULL
    requires n >= 1;
    requires \valid(vp_avoid_buf) && \base_addr(vp_avoid_buf) != \base_addr((char *)p);
    assigns \result \from p, n;
    allocates \result;
    ensures \result != \null && \valid((char *)\result + (0 .. n - 1));
    // realloc keeps the old bytes; stated for the one element type it is used
    // with here (infoptr_T, 24 bytes), which follows from keeping the bytes.
    ensures \separated((char *)\result + (0 .. n - 1), vp_avoid_buf);
    ensures \forall integer i; 0 <= i && (i + 1) * 24 <= n && \valid_read{Pre}((infoptr_T *)p + i) ==>
              ((infoptr_T *)\result)[i] == \at(((infoptr_T *)p)[i], Pre);
*/
void *xrealloc(void *p, size_t n);

/*@ requires vp_nfree < 1024;
    assigns vp_nfree, vp_freelog[vp_nfree];
    ensures vp_nfree == \old(vp_nfree) + 1 && vp_freelog[\old(vp_nfree)] == p;
*/
void xfree(void *p);

/*@ // path.c FullName_save (not verified here): a new string, or NULL
    assigns \result \from fname[0 ..], force;
    allocates \result;
    ensures \result == \null || \forall char *q; \valid_read{Pre}(q) ==> \base_addr(q) != \base_addr(\result);
*/
char *FullName_save(const char *fname, bool force);

/*@ // memfile.c mf_new (not yet verified; see ../PLAN.md): a block of
    // mf_page_size * page_count bytes, separate from mfp. Pages are never smaller
    // than a DataBlock header (MIN_SWAP_PAGE_SIZE is 1048).
    requires \valid(mfp) && page_count >= 1 && mfp->mf_page_size >= 24;
    assigns *mfp, \result \from *mfp, negative, page_count;
    ensures \valid(\result) && \separated(\result, mfp);
    ensures \result->bh_page_count == page_count;
    // (stated field by field: WP drops \valid on a struct with a flexible array)
    ensures \let dp = (DataBlock *)\result->bh_data;
      \valid(&dp->db_id) && \valid(&dp->db_free) && \valid(&dp->db_txt_start) &&
      \valid(&dp->db_txt_end) && \valid(&dp->db_line_count) &&
      \separated(&dp->db_id, &dp->db_free, &dp->db_txt_start, &dp->db_txt_end,
                 &dp->db_line_count, \result, mfp);
    ensures \let pp = (PointerBlock *)\result->bh_data;
      \valid(&pp->pb_id) && \valid(&pp->pb_count) && \valid(&pp->pb_count_max) &&
      \separated(&pp->pb_id, &pp->pb_count, &pp->pb_count_max, \result, mfp);
    ensures mfp->mf_page_size == \old(mfp->mf_page_size);
*/
bhdr_T *mf_new(memfile_T *mfp, bool negative, unsigned page_count);

/*@ // mbyte.c mb_utflen (not verified here): adds the number of code points and
    // UTF-16 code units of s[0 .. len-1] to the two counters. vp_cps / vp_cus are
    // uninterpreted: this file relies only on "adds something that depends on the bytes".
    logic integer vp_cps{L}(char *s, integer len) reads s[0 .. len - 1];
    logic integer vp_cus{L}(char *s, integer len) reads s[0 .. len - 1];
*/
/*@ requires \valid_read(s + (0 .. len - 1)) && \valid(codepoints) && \valid(codeunits);
    requires \separated(codepoints, codeunits);
    requires *codepoints + vp_cps(s, len) <= SIZE_MAX && *codeunits + vp_cus(s, len) <= SIZE_MAX;
    assigns *codepoints, *codeunits \from s[0 .. len - 1], len, *codepoints, *codeunits;
    ensures *codepoints == \old(*codepoints) + vp_cps(s, len);
    ensures *codeunits == \old(*codeunits) + vp_cus(s, len);
*/
void mb_utflen(const char *s, size_t len, size_t *codepoints, size_t *codeunits);

/*@ // ml_get_buf_impl / ml_get_buf_len (memline.c, not yet verified): the text of
    // line lnum of buf (vp_line, uninterpreted) and its length vp_len, a string
    // with vp_len readable bytes before its NUL. will_change asks for a writable copy.
    logic char *vp_line{L}(buf_T *buf, integer lnum, integer will_change);
    logic integer vp_len{L}(buf_T *buf, integer lnum);
*/
/*@ requires \valid(buf);
    assigns \result \from buf, lnum, will_change;
    ensures \result == vp_line(buf, lnum, will_change) && \result != \null;
    ensures 0 <= vp_len(buf, lnum) && \valid_read(\result + (0 .. vp_len(buf, lnum)));
*/
static char *ml_get_buf_impl(buf_T *buf, linenr_T lnum, bool will_change);
/*@ requires \valid(buf);
    assigns \result \from buf, lnum;
    ensures \result == vp_len(buf, lnum) && 0 <= \result;
*/
colnr_T ml_get_buf_len(buf_T *buf, linenr_T lnum);

// The editing entry points below are not yet verified. vp_world stands for all
// the state they change; their results are uninterpreted functions of the call.
// The wrappers are proved to pass the right arguments and return the result.
/*@ ghost int vp_world; */
/*@ ghost buf_T *vp_upd_buf; */
/*@ ghost int vp_upd_what; */
/*@ logic integer vp_append{L}(integer lnum, char *line, integer len, integer flags);
    logic integer vp_replace{L}(buf_T *buf, integer lnum, char *line, integer copy, integer noalloc);
    logic integer vp_replace_len{L}(buf_T *buf, integer lnum, char *line, integer len, integer copy, integer noalloc);
    logic integer vp_delete{L}(integer lnum, integer flags);
*/
#define ML_APPEND_NEW 1
typedef enum { UB_FNAME = 0, UB_SAME_DIR } upd_block0_T;
/*@ assigns vp_world; ensures \result == vp_append{Pre}(lnum, line, len, flags); */
int ml_append_flags(linenr_T lnum, char *line, colnr_T len, int flags);
/*@ assigns vp_world; ensures \result == vp_replace{Pre}(buf, lnum, line, copy, noalloc); */
int ml_replace_buf(buf_T *buf, linenr_T lnum, char *line, bool copy, bool noalloc);
/*@ assigns vp_world; ensures \result == vp_replace_len{Pre}(buf, lnum, line_arg, len_arg, copy, noalloc); */
int ml_replace_buf_len(buf_T *buf, linenr_T lnum, char *line_arg, size_t len_arg, bool copy, bool noalloc);
/*@ assigns vp_world; ensures \result == vp_delete{Pre}(lnum, flags); */
int ml_delete_flags(linenr_T lnum, int flags);
/*@ assigns vp_world, vp_upd_buf, vp_upd_what; ensures vp_upd_buf == buf && vp_upd_what == what; */
static void ml_upd_block0(buf_T *buf, upd_block0_T what);

// ---------------------------------------------------------------- proved
/*@ // proved below with the functions (run label "lemmas"): a product of two
    // unsigned ints never wraps a 64-bit size_t.
    lemma vp_u32_mul_fits: \forall integer a, b; 0 <= a <= UINT_MAX && 0 <= b <= UINT_MAX ==>
      0 <= a * b <= SIZE_MAX;
*/
/*@ requires \valid(mfp);
    assigns mfp->mf_page_size;
    ensures mfp->mf_page_size == new_size;
*/
void mf_new_page_size(memfile_T *mfp, unsigned new_size);

/*@ requires \valid_read(mfp) && page_count >= 1 && mfp->mf_page_size >= 1;
    assigns \result \from mfp->mf_page_size, page_count;
    assigns \at(\result, Post)->bh_data, \at(\result, Post)->bh_page_count;   // the new header only
    ensures \valid(\result) && \result->bh_page_count == page_count;
    ensures \valid((char *)\result->bh_data + (0 .. (integer)\old(mfp->mf_page_size) * page_count - 1));
*/
static bhdr_T *mf_alloc_bhdr(memfile_T *mfp, unsigned page_count);

/*@ requires \valid(hp) && vp_nfree < 1023;
    assigns vp_nfree, vp_freelog[vp_nfree], vp_freelog[vp_nfree + 1];
    ensures vp_nfree == \old(vp_nfree) + 2;
    ensures vp_freelog[\old(vp_nfree)] == \old(hp->bh_data);   // data first
    ensures vp_freelog[\old(vp_nfree) + 1] == hp;              // then the header
*/
static void mf_free_bhdr(bhdr_T *hp);

/*@ requires \valid(mfp) && \valid(hp) && \separated(mfp, hp);
    assigns hp->bh_data, mfp->mf_free_first;
    ensures mfp->mf_free_first == hp && hp->bh_data == \old(mfp->mf_free_first);
*/
static void mf_ins_free(memfile_T *mfp, bhdr_T *hp);

/*@ requires \valid(mfp) && mfp->mf_free_first != \null;   // documented: caller checks
    requires \valid_read(mfp->mf_free_first);
    assigns mfp->mf_free_first;
    ensures \result == \old(mfp->mf_free_first);
    ensures mfp->mf_free_first == \old(mfp->mf_free_first->bh_data);
*/
static bhdr_T *mf_rem_free(memfile_T *mfp);

/*@ requires \valid_read(mfp);
    assigns \nothing;
    ensures \result <==> (mfp->mf_fname != \null && mfp->mf_neg_count > 0);
*/
bool mf_need_trans(memfile_T *mfp);

/*@ // An empty data block: text area empty at the end of the block, free space
    // is everything after the header. Callers (ml_append_int) give page counts
    // from an int-sized line length, so the block size fits in unsigned.
    requires \valid(mfp) && 1 <= page_count <= UINT_MAX && mfp->mf_page_size >= 24;
    requires page_count * mfp->mf_page_size <= UINT_MAX;
    assigns *mfp, \result, ((DataBlock *)\result->bh_data)->db_id,
            ((DataBlock *)\result->bh_data)->db_txt_start, ((DataBlock *)\result->bh_data)->db_txt_end,
            ((DataBlock *)\result->bh_data)->db_free, ((DataBlock *)\result->bh_data)->db_line_count;
    ensures \valid(\result) && \result->bh_page_count == page_count;
    ensures \let dp = (DataBlock *)\result->bh_data;
      dp->db_id == DATA_ID && dp->db_line_count == 0 &&
      dp->db_txt_start == page_count * mfp->mf_page_size &&
      dp->db_txt_end == page_count * mfp->mf_page_size &&
      dp->db_free == page_count * mfp->mf_page_size - 24;
*/
static bhdr_T *ml_new_data(memfile_T *mfp, bool negative, int64_t page_count);

/*@ // An empty pointer block of one page; pb_count_max = how many PointerEntry
    // fit after the header, which fits in uint16_t for pages up to 1 MiB.
    requires \valid(mfp) && mfp->mf_page_size >= 24;
    assigns *mfp, \result, ((PointerBlock *)\result->bh_data)->pb_id,
            ((PointerBlock *)\result->bh_data)->pb_count, ((PointerBlock *)\result->bh_data)->pb_count_max;
    ensures \valid(\result) && \result->bh_page_count == 1;
    ensures \let pp = (PointerBlock *)\result->bh_data;
      pp->pb_id == PTR_ID && pp->pb_count == 0 &&
      ((mfp->mf_page_size - 8) / 24 <= 65535 ==>
        pp->pb_count_max == (mfp->mf_page_size - 8) / 24);
*/
static bhdr_T *ml_new_ptr(memfile_T *mfp);

/*@ // Push one entry: return the old top; grow by STACK_INCR when full, keeping
    // the existing entries.
    requires \valid(buf);
    requires 0 <= buf->b_ml.ml_stack_top <= buf->b_ml.ml_stack_size <= INT_MAX - STACK_INCR;
    requires \valid(buf->b_ml.ml_stack + (0 .. buf->b_ml.ml_stack_size - 1));
    requires \base_addr(buf) != \base_addr(buf->b_ml.ml_stack);   // the stack is its own allocation
    requires vp_avoid_buf == buf;   // ghost: realloc result is separate from buf
    assigns buf->b_ml;
    ensures \result == \old(buf->b_ml.ml_stack_top);
    ensures buf->b_ml.ml_stack_top == \old(buf->b_ml.ml_stack_top) + 1;
    ensures buf->b_ml.ml_stack_top <= buf->b_ml.ml_stack_size;
    ensures \valid(buf->b_ml.ml_stack + (0 .. buf->b_ml.ml_stack_size - 1));
    ensures \forall integer i; 0 <= i < \old(buf->b_ml.ml_stack_top) ==>
              buf->b_ml.ml_stack[i] == \old(buf->b_ml.ml_stack[i]);
*/
static int ml_add_stack(buf_T *buf);

/*@ requires \valid(mfp) && vp_nfree < 1023;
    assigns vp_nfree, vp_freelog[vp_nfree], vp_freelog[vp_nfree + 1], mfp->mf_fname, mfp->mf_ffname;
    ensures vp_nfree == \old(vp_nfree) + 2;
    ensures vp_freelog[\old(vp_nfree)] == \old(mfp->mf_fname);
    ensures vp_freelog[\old(vp_nfree) + 1] == \old(mfp->mf_ffname);
    ensures mfp->mf_fname == \null && mfp->mf_ffname == \null;
*/
void mf_free_fnames(memfile_T *mfp);

/*@ requires \valid(mfp) && \valid_read(fname);   // fname: an allocated string (documented)
    assigns mfp->mf_fname, mfp->mf_ffname;
    ensures mfp->mf_fname == fname;
    ensures mfp->mf_ffname == \null || \base_addr(mfp->mf_ffname) != \base_addr(fname);
*/
void mf_set_fnames(memfile_T *mfp, char *fname);

/*@ // Return the counts gathered since the last flush and reset them to zero.
    requires \valid(buf) && \valid(codepoints) && \valid(codeunits);
    requires \separated(buf, codepoints, codeunits);
    assigns *codepoints, *codeunits, buf->deleted_bytes, buf->deleted_codepoints, buf->deleted_codeunits;
    ensures \result == \old(buf->deleted_bytes);
    ensures *codepoints == \old(buf->deleted_codepoints) && *codeunits == \old(buf->deleted_codeunits);
    ensures buf->deleted_bytes == 0 && buf->deleted_codepoints == 0 && buf->deleted_codeunits == 0;
*/
size_t ml_flush_deleted_bytes(buf_T *buf, size_t *codepoints, size_t *codeunits);

/*@ // Nonzero iff the cached line of curbuf was changed (and so is allocated).
    requires \valid_read(curbuf);
    assigns \nothing;
    ensures (\result != 0) <==> ((curbuf->b_ml.ml_flags & ML_LINE_DIRTY) != 0);
    ensures \result == (curbuf->b_ml.ml_flags & ML_LINE_DIRTY);
*/
int ml_line_alloced(void);

/*@ // Count a deleted line: its length (len, or the whole string when len is -1 or
    // too big) plus one for the NL, in bytes, and when asked in code points/units.
    // Callers pass -1 or a length >= 0; no counter wraps.
    requires \valid(buf) && is_str(ptr) && len >= -1;
    requires \separated(buf, ptr + (0 ..));
    requires \valid_read(&inhibit_delete_count) && \separated(&inhibit_delete_count, buf);
    requires \forall integer m; str_len(ptr, m) ==> m <= PTRDIFF_MAX;   // no object is larger
    requires \forall integer m; str_len(ptr, m) ==> buf->deleted_bytes + m + 1 <= SIZE_MAX;
    requires \forall integer m; str_len(ptr, m) ==> buf->deleted_bytes2 + m + 1 <= SIZE_MAX;
    requires buf->update_need_codepoints ==> \forall integer m; str_len(ptr, m) ==>
      \forall integer n; 0 <= n <= m ==>
        buf->deleted_codepoints + vp_cps(ptr, n) + 1 <= SIZE_MAX &&
        buf->deleted_codeunits + vp_cus(ptr, n) + 1 <= SIZE_MAX;
    assigns buf->deleted_bytes, buf->deleted_bytes2, buf->deleted_codepoints, buf->deleted_codeunits;
    behavior inhibited:
      assumes inhibit_delete_count != 0;
      ensures buf->deleted_bytes == \old(buf->deleted_bytes) && buf->deleted_bytes2 == \old(buf->deleted_bytes2);
      ensures buf->deleted_codepoints == \old(buf->deleted_codepoints);
      ensures buf->deleted_codeunits == \old(buf->deleted_codeunits);
    behavior counted:
      assumes inhibit_delete_count == 0;
      ensures \forall integer m; str_len{Pre}(ptr, m) ==> \let n = (len == -1 || len > m) ? m : len;
        buf->deleted_bytes == \old(buf->deleted_bytes) + n + 1 &&
        buf->deleted_bytes2 == \old(buf->deleted_bytes2) + n + 1 &&
        (buf->update_need_codepoints ==>
          buf->deleted_codepoints == \old(buf->deleted_codepoints) + vp_cps(ptr, n) + 1 &&
          buf->deleted_codeunits == \old(buf->deleted_codeunits) + vp_cus(ptr, n) + 1) &&
        (!buf->update_need_codepoints ==>
          buf->deleted_codepoints == \old(buf->deleted_codepoints) &&
          buf->deleted_codeunits == \old(buf->deleted_codeunits));
    complete behaviors; disjoint behaviors;
*/
void ml_add_deleted_len_buf(buf_T *buf, char *ptr, ssize_t len);

/*@ requires \valid(curbuf) && is_str(ptr) && len >= -1;
    requires \separated(curbuf, ptr + (0 ..));
    requires \valid_read(&inhibit_delete_count) && \separated(&inhibit_delete_count, curbuf);
    requires \forall integer m; str_len(ptr, m) ==> m <= PTRDIFF_MAX;   // no object is larger
    requires \forall integer m; str_len(ptr, m) ==> curbuf->deleted_bytes + m + 1 <= SIZE_MAX;
    requires \forall integer m; str_len(ptr, m) ==> curbuf->deleted_bytes2 + m + 1 <= SIZE_MAX;
    requires curbuf->update_need_codepoints ==> \forall integer m; str_len(ptr, m) ==>
      \forall integer n; 0 <= n <= m ==>
        curbuf->deleted_codepoints + vp_cps(ptr, n) + 1 <= SIZE_MAX &&
        curbuf->deleted_codeunits + vp_cus(ptr, n) + 1 <= SIZE_MAX;
    assigns curbuf->deleted_bytes, curbuf->deleted_bytes2, curbuf->deleted_codepoints, curbuf->deleted_codeunits;
    ensures inhibit_delete_count == 0 ==> \forall integer m; str_len{Pre}(ptr, m) ==>
      \let n = (len == -1 || len > m) ? m : len;
        curbuf->deleted_bytes == \old(curbuf->deleted_bytes) + n + 1;
    ensures inhibit_delete_count != 0 ==> curbuf->deleted_bytes == \old(curbuf->deleted_bytes);
*/
void ml_add_deleted_len(char *ptr, ssize_t len);

/*@ requires \valid(curbuf);
    assigns \nothing;
    ensures \result == vp_line(curbuf, lnum, 0);
*/
char *ml_get(linenr_T lnum);

/*@ requires \valid(buf);
    assigns \nothing;
    ensures \result == vp_line(buf, lnum, 0);
*/
char *ml_get_buf(buf_T *buf, linenr_T lnum);

/*@ requires \valid(buf);
    assigns \nothing;
    ensures \result == vp_line(buf, lnum, 1);
*/
char *ml_get_buf_mut(buf_T *buf, linenr_T lnum);

/*@ // pointer to column col of the line; col must lie within the line (or at its NUL)
    requires \valid(curbuf) && \valid_read(pos);
    requires 0 <= pos->col <= vp_len(curbuf, pos->lnum);
    assigns \nothing;
    ensures \result == vp_line(curbuf, pos->lnum, 0) + pos->col;
*/
char *ml_get_pos(const pos_T *pos);

/*@ // bytes from column col to the end of the line
    requires \valid(curbuf) && \valid_read(pos);
    requires 0 <= pos->col <= vp_len(curbuf, pos->lnum);
    assigns \nothing;
    ensures \result == vp_len(curbuf, pos->lnum) - pos->col;
*/
colnr_T ml_get_pos_len(pos_T *pos);

/*@ assigns vp_world;
    ensures \result == vp_append{Pre}(lnum, line, len, newfile ? ML_APPEND_NEW : 0); */
int ml_append(linenr_T lnum, char *line, colnr_T len, bool newfile);
/*@ assigns vp_world;
    ensures \result == vp_replace{Pre}(curbuf, lnum, line, copy, 0); */
int ml_replace(linenr_T lnum, char *line, bool copy);
/*@ assigns vp_world;
    ensures \result == vp_replace_len{Pre}(curbuf, lnum, line, len, copy, 0); */
int ml_replace_len(linenr_T lnum, char *line, size_t len, bool copy);
/*@ assigns vp_world;
    ensures \result == vp_delete{Pre}(lnum, 0); */
int ml_delete(linenr_T lnum);
/*@ assigns vp_world, vp_upd_buf, vp_upd_what;
    ensures vp_upd_buf == buf && vp_upd_what == UB_FNAME; */
void ml_timestamp(buf_T *buf);
