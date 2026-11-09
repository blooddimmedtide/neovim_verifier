// Contracts for what garray.c calls outside itself. Everything here is trusted
// (listed in ../CLAIM.md); no axioms are used.
#ifndef VP_GARRAY_H
#define VP_GARRAY_H
#include <stddef.h>
#include <stdint.h>
#include <limits.h>
#include "vp_string.h"

// Allocation state. WP ignores \fresh-based frees, so ghost variables track it:
// vp_live counts live allocations; every xfree call is logged in order in
// vp_freelog[0 .. vp_nfree - 1] (NULL included), so a contract can say exactly
// which pointers a function frees.
/*@ ghost long vp_live; */
/*@ ghost size_t vp_nfree; */
// vp_oom: whether an allocation may run out of memory (then memory.c calls
// preserve_exit()). Never assigned: contracts say "exits when vp_oom or <cond>", so with
// vp_oom false they state exactly when a function exits.
/*@ ghost int vp_oom; */
/*@ ghost void *vp_freelog[4294967296]; */


/*@ // Neovim's xrealloc (memory.c): realloc of max(n, 1) bytes; on failure it
    // frees memory and retries, then calls preserve_exit(): it never returns NULL.
    // `old` (ghost) is how many leading bytes the caller relies on keeping.
    requires p == \null || \valid((char *)p + (0 .. old - 1));
    requires vp_live < LONG_MAX;
    // a1, a2 (ghost): live blocks the caller names; the result overlaps neither. (WP does not
    // model allocation: "differs from every block readable before" would be contradictory.)
    requires \valid_read(a1) && \valid_read(a2);
    requires p != \null ==> \base_addr((char *)p) != \base_addr(a1) && \base_addr((char *)p) != \base_addr(a2);
    assigns \result \from p, n;
    assigns vp_live;
    allocates \result;
    ensures \result != \null && \valid((char *)\result + (0 .. n - 1));
    ensures \forall integer i; 0 <= i < old && i < n ==> ((char *)\result)[i] == \old(((char *)p)[i]);
    ensures \base_addr((char *)\result) != \base_addr(a1) && \base_addr((char *)\result) != \base_addr(a2);
    ensures vp_live == \old(vp_live) + (p == \null ? 1 : 0);
    exits vp_oom;   // preserve_exit() when memory runs out
*/
void *xrealloc(void *p, size_t n) /*@ ghost (size_t old, char *a1, char *a2) */;

/*@ requires vp_nfree < 4294967296;
    requires p != \null ==> vp_live > LONG_MIN;
    assigns vp_live, vp_nfree, vp_freelog[vp_nfree];
    ensures vp_nfree == \old(vp_nfree) + 1 && vp_freelog[\old(vp_nfree)] == p;
    ensures vp_live == \old(vp_live) - (p == \null ? 0 : 1);
*/
void xfree(void *p);

/*@ // xmallocz (memory.c): size + 1 bytes, last one NUL; preserve_exit() if size + 1 wraps
    requires vp_live < LONG_MAX;
    // the result overlaps none of the named live blocks: arr, arr[0 .. cnt-1], sp (ghost)
    requires \valid_read(arr + (0 .. cnt - 1)) && \valid_read(sp)
             && \forall integer k; 0 <= k < cnt ==> \valid_read(arr[k]);
    assigns \result \from size;
    assigns vp_live;
    allocates \result;
    exits vp_oom || size == SIZE_MAX;   // out of memory, or size + 1 wraps
    behavior fits:
      assumes size < SIZE_MAX;
      ensures \result != \null && \valid((char *)\result + (0 .. size)) && ((char *)\result)[size] == 0;
      ensures \base_addr((char *)\result) != \base_addr((char *)arr) && \base_addr((char *)\result) != \base_addr(sp)
              && \forall integer k; 0 <= k < cnt ==> \base_addr((char *)\result) != \base_addr(\at(arr[k], Pre));
      ensures vp_live == \old(vp_live) + 1;
    behavior too_big:
      assumes size == SIZE_MAX;
      ensures \false;
    complete behaviors; disjoint behaviors;
*/
void *xmallocz(size_t size) /*@ ghost (char **arr, size_t cnt, char *sp) */;

/*@ // xstrdup (memory.c): a new copy of the string
    requires str_len((char *)str, n) && n < SIZE_MAX;
    requires vp_live < LONG_MAX;
    assigns \result \from ((char *)str)[0 .. n];
    assigns vp_live;
    allocates \result;
    ensures \result != \null && str_len(\result, n)
            && \forall integer i; 0 <= i <= n ==> \result[i] == \old(str[i]);
    ensures vp_live == \old(vp_live) + 1;
    exits vp_oom;   // preserve_exit() when memory runs out
*/
char *xstrdup(const char *str) /*@ ghost (size_t n) */;

/*@ // the contract proved for xstpcpy in ../../memory (memory/wp/contracts.py)
    requires n < PTRDIFF_MAX;
    requires str_len((char *)src, n) && \valid(dst + (0 .. n)) && \separated(dst + (0 .. n), src + (0 .. n));
    assigns dst[0 .. n];
    ensures \result == dst + n && \forall integer i; 0 <= i <= n ==> dst[i] == \at(src[i], Pre);
*/
char *xstpcpy(char *restrict dst, const char *restrict src) /*@ ghost (size_t n) */;

/*@ // C11 7.24.2.3
    requires str_len((char *)src, n) && \valid(dst + (0 .. n)) && \separated(dst + (0 .. n), src + (0 .. n));
    assigns dst[0 .. n];
    ensures \result == dst && \forall integer i; 0 <= i <= n ==> dst[i] == \at(src[i], Pre);
*/
char *strcpy(char *restrict dst, const char *restrict src) /*@ ghost (size_t n) */;

/*@ // preserve_exit (main.c): writes swap files and exits; never returns
    assigns \nothing;
    exits \true;
    ensures \false;
*/
void preserve_exit(const char *errmsg);

/*@ // emsg (message.c): shows an error message; touches no growarray
    assigns \nothing;
*/
int emsg(const char *s);

/*@ // WLOG(...) (log.h, logmsg at warning level): writes the log file only
    assigns \nothing;
*/
void vp_wlog(void);
// path_equal() flags, as src/nvim/path.h defines them (build.py checks the text)
typedef enum {
  kPathCmpLiteral = 1 << 0,  ///< Compare paths literally.
  kPathCmpExpand  = 1 << 1,  ///< Expand env vars in the first path.
  kPathCmpFull    = 1 << 2,  ///< Compare full names when FileIds are unavailable.
} PathCmpFlags;
extern int p_fic;  // 'fileignorecase' (option_vars.h), read by path_equal
extern void *capture_ga;  // message.c: the growing array output is captured into, or NULL

/*@ // The order sort_strings() (strings.c: qsort with strcmp) gives a[0 .. n-1].
    // Uninterpreted: the proof holds for whatever order it produces.
    logic char *vp_sorted{L}(char **a, integer n, integer k);
    // path_equal(a, b, kPathCmpLiteral) (path.c). Uninterpreted; it depends only
    // on the bytes of both strings and 'fileignorecase'.
    predicate vp_path_eq{L}(char *a, char *b) reads a[0 ..], b[0 ..], p_fic;
*/

/*@ requires 0 <= count && \valid(files + (0 .. count - 1));
    requires \forall integer k; 0 <= k < count ==> is_str(files[k]);
    assigns files[0 .. count - 1];
    ensures \forall integer k; 0 <= k < count ==> files[k] == vp_sorted{Pre}(files, count, k);
    ensures \forall integer k; 0 <= k < count ==> is_str(files[k]);   // a permutation of strings
*/
void sort_strings(char **files, int count);

/*@ requires is_str((char *)s1) && is_str((char *)s2) && flags == kPathCmpLiteral;
    assigns \nothing;
    ensures \result != 0 <==> vp_path_eq((char *)s1, (char *)s2);
*/
_Bool path_equal(const char *s1, const char *s2, PathCmpFlags flags);
#endif
