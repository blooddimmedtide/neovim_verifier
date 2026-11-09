#define FUNC_ATTR_NONNULL_ARG(...)
// Stubs for the callees of find_special_key outside keycodes.c. Each returns any value the
// real function can return (over-approximation), so a property proved here holds for the
// real callees too. Facts used: vim_str2nr sets *len >= 0 and any *unptr; utf_ptr2char
// returns a value in [0, INT_MAX] (mbyte CBMC: the code point or the first byte);
// utfc_ptr2len* return a length >= 1 that stays inside the string (0 at NUL).
typedef int64_t varnumber_T;
typedef uint64_t uvarnumber_T;
#define STR2NR_ALL 15
#define NUL '\000'
#define _(x) ((char *)(x))
static const char e_invarg[] = "E474";
static void emsg(const char *m) { (void)m; }
int nondet_int(void); uint64_t nondet_u64(void);
static size_t vp_strlen(const char *p) { size_t n = 0; while (p[n]) n++; return n; }
static void vim_str2nr(const char *const start, int *const prep, int *const len, const int what,
                       varnumber_T *const nptr, uvarnumber_T *const unptr, const int maxlen,
                       const bool strict, bool *const overflow) {
  int l = nondet_int(); __CPROVER_assume(l >= 0 && (size_t)l <= vp_strlen(start)); *len = l;
  if (unptr) *unptr = nondet_u64();
}
static int utf_ptr2char(const char *p) { int c = nondet_int(); __CPROVER_assume(c >= 0); return c; }
static int utfc_ptr2len(const char *p) {
  if (*p == 0) return 0;
  int l = nondet_int(); __CPROVER_assume(l >= 1 && (size_t)l <= vp_strlen(p)); return l;
}
static int utfc_ptr2len_len(const char *p, int size) {
  int l = nondet_int(); __CPROVER_assume(l >= 1 && (size <= 0 || l <= size)); return l;
}
#define STRNICMP(d, s, n) vim_strnicmp_asc((char *)(d), (char *)(s), (n))
int vp_real_simplify_key(const int key, int *modifiers);
int simplify_key(const int key, int *modifiers) {
  __CPROVER_assert(key != INT_MIN, "simplify_key gets key != INT_MIN");
  return vp_real_simplify_key(key, modifiers);
}
