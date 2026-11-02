// C-library functions that fzf.c calls and CBMC 6.4.1 has no usable body for.
// glibc's <ctype.h> macros go through __ctype_b_loc (no body in CBMC), so the
// harnesses are compiled with -D__NO_CTYPE and get these functions instead.
// strtok and strstr have no CBMC model at all. Everything else (strlen,
// strncmp, strcmp, strchr, strdup, strncpy, strcpy, malloc, realloc, free,
// memset) is CBMC's own library model.
//
// These are the C11 definitions in the "C" locale (7.4.1.10, 7.4.2.1,
// 7.24.5.7, 7.24.5.8). difftest/libc_check.c compares each one with glibc in
// the C locale over all inputs up to a bound. CLAIM.md: the proof holds for a
// process whose LC_CTYPE classifies bytes like the C locale (true for every
// UTF-8 locale of glibc, which Neovim uses; NOT for single-byte Latin-1 locales).
#include <stddef.h>

int isspace(int c) {
  return c == ' ' || c == '\t' || c == '\n' || c == '\v' || c == '\f' || c == '\r';
}

int tolower(int c) {
  return (c >= 'A' && c <= 'Z') ? c - 'A' + 'a' : c;
}

static int fzfv_in(char c, const char *set) {
  for (; *set; set++)
    if (*set == c) return 1;
  return 0;
}

char *strtok(char *s, const char *delim) {
  static char *next;
  if (s) next = s;
  if (!next) return NULL;
  while (*next && fzfv_in(*next, delim)) next++;   // skip leading delimiters
  if (!*next) { next = NULL; return NULL; }
  char *tok = next;
  while (*next && !fzfv_in(*next, delim)) next++;  // token ends at a delimiter or NUL
  if (*next) { *next = 0; next++; } else next = NULL;
  return tok;
}

char *strstr(const char *hay, const char *needle) {
  for (;; hay++) {
    size_t i = 0;
    while (needle[i] && hay[i] == needle[i]) i++;
    if (!needle[i]) return (char *)hay;
    if (!*hay) return NULL;
  }
}

// CBMC 6.4.1's own memset leaves bytes unset when the size is symbolic and the
// object is not a char array (an int16_t[2] object memset to 0 keeps a nonzero
// byte: false alarms, so its model cannot be trusted either way). These
// byte-by-byte C11 definitions replace every string/memory function fzf.c
// uses; only malloc, realloc and free stay CBMC's.
void *memset(void *s, int c, size_t n) {
  unsigned char *p = s;
  for (size_t i = 0; i < n; i++) p[i] = (unsigned char)c;
  return s;
}
size_t strlen(const char *s) {
  size_t n = 0;
  while (s[n]) n++;
  return n;
}
int strncmp(const char *a, const char *b, size_t n) {
  for (size_t i = 0; i < n; i++) {
    unsigned char x = (unsigned char)a[i], y = (unsigned char)b[i];
    if (x != y) return x < y ? -1 : 1;
    if (x == 0) return 0;
  }
  return 0;
}
int strcmp(const char *a, const char *b) {
  for (size_t i = 0;; i++) {
    unsigned char x = (unsigned char)a[i], y = (unsigned char)b[i];
    if (x != y) return x < y ? -1 : 1;
    if (x == 0) return 0;
  }
}
char *strchr(const char *s, int c) {
  for (;; s++) {
    if (*s == (char)c) return (char *)s;
    if (!*s) return NULL;
  }
}
char *strcpy(char *d, const char *s) {
  size_t i = 0;
  for (; s[i]; i++) d[i] = s[i];
  d[i] = 0;
  return d;
}
char *strncpy(char *d, const char *s, size_t n) {
  size_t i = 0;
  for (; i < n && s[i]; i++) d[i] = s[i];
  for (; i < n; i++) d[i] = 0;
  return d;
}
void *malloc(size_t);
void free(void *);
char *strdup(const char *s) {
  size_t n = strlen(s);
#ifdef STRDUP_MAX   // constant-size branches, as in harness_util.h (asserted bound)
  __CPROVER_assert(n + 1 <= STRDUP_MAX, "strdup size within the model's bound");
  __CPROVER_assume(n + 1 <= STRDUP_MAX);
  char *d = NULL;
  for (size_t k = 0; k <= STRDUP_MAX; k++)
    if (n + 1 == k) d = malloc(k);
#else
  char *d = malloc(n + 1);
#endif
  if (d) strcpy(d, s);
  return d;
}
// realloc: CBMC's model by default (its copy is checked by h_append_pos /
// h_insert_range: "old kept"). Where realloc gets a symbolic size several times
// on one path, CBMC's SAT encoding runs out of memory, so two sound variants:
//  - REALLOC_UNREACHABLE: realloc must not be called at all (asserted); used
//    by the algorithm harnesses, whose position arrays have room.
//  - REALLOC_MAX=k: sizes up to k bytes (asserted), each allocated in its own
//    branch with a constant size, contents copied byte by byte.
#if defined(REALLOC_UNREACHABLE)
void *realloc(void *p, size_t n) {
  __CPROVER_assert(0, "realloc is not reached in this harness");
  __CPROVER_assume(0);
  return p;
}
#elif defined(REALLOC_MAX)
void *realloc(void *p, size_t n) {
  // every realloc in fzf.c asks for a multiple of 4 bytes (uint32_t
  // positions, 8-byte pointers, 40-byte terms): asserted, then one branch per
  // multiple of 4 up to the bound
  __CPROVER_assert(n <= REALLOC_MAX && n % 4 == 0, "realloc size within the model's bound");
  __CPROVER_assume(n <= REALLOC_MAX && n % 4 == 0);
  unsigned char *q = NULL;
  for (size_t k = 0; k <= REALLOC_MAX; k += 4)
    if (n == k) q = malloc(k);
  if (p) {
    size_t old = __CPROVER_OBJECT_SIZE(p);
    __CPROVER_assert(__CPROVER_POINTER_OFFSET(p) == 0 && __CPROVER_r_ok(p, old), "realloc of a live heap block");
    for (size_t i = 0; i < REALLOC_MAX && i < n && i < old; i++) q[i] = ((unsigned char *)p)[i];
    free(p);
  }
  return q;
}
#endif
