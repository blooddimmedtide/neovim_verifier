// Differential test: garray.c (the exact text the proof uses, built by ../wp/build.py),
// compiled by gcc under ASan/UBSan, against references written from ../CLAIM.md.
// Usage: ./difftest <iterations> <seed>
#include <limits.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static long frees, allocs;
static jmp_buf exit_jb;
void *xrealloc(void *p, size_t n) { if (!p) allocs++; void *r = realloc(p, n ? n : 1); if (!r) abort(); return r; }
void xfree(void *p) { if (p) frees++; free(p); }
void *xmallocz(size_t n) { allocs++; char *r = malloc(n + 1); if (!r) abort(); r[n] = 0; return r; }
char *xstrdup(const char *s) { allocs++; char *r = strdup(s); if (!r) abort(); return r; }
char *xstpcpy(char *restrict d, const char *restrict s) { size_t n = strlen(s); return (char *)memcpy(d, s, n + 1) + n; }
void preserve_exit(const char *m) { (void)m; longjmp(exit_jb, 1); }
static int emsgs;
int emsg(const char *s) { (void)s; emsgs++; return 1; }
void vp_wlog(void) {}
const char e_resulting_text_too_long[] = "E1240: Resulting text too long";
int p_fic;
static int cmp(const void *a, const void *b) { return strcmp(*(char **)a, *(char **)b); }
// strings.c passes count 0 with files == NULL straight to qsort (see ../CLAIM.md); skip that here
void sort_strings(char **files, int count) { if (count == 0) return; qsort((void *)files, (size_t)count, sizeof(char *), cmp); }
_Bool path_equal(const char *a, const char *b, int flags) { (void)flags; return strcmp(a, b) == 0; }
#define path_equal(a, b, f) path_equal(a, b, (int)(f))
#include GA_C

static unsigned long long s;
static unsigned rnd(void) { s ^= s << 13; s ^= s >> 7; s ^= s << 17; return (unsigned)(s >> 11); }
static unsigned long fails, checks, it;
#define CHECK(cond, what) do { checks++; if (!(cond)) { if (fails++ < 20) printf("MISMATCH %s (iter %lu)\n", what, it); } } while (0)
static long imax(long a, long b) { return a > b ? a : b; }

int main(int argc, char **argv) {
  unsigned long iters = argc > 1 ? strtoul(argv[1], 0, 0) : 100000;
  s = argc > 2 ? strtoull(argv[2], 0, 0) : 0x9e3779b97f4a7c15ull;
  for (it = 0; it < iters; it++) {
    // ga_init / ga_set_growsize
    garray_T ga; int gs = (int)(rnd() % 12) - 3;
    ga_init(&ga, 1, gs);
    CHECK(ga.ga_data == NULL && ga.ga_len == 0 && ga.ga_maxlen == 0 && ga.ga_itemsize == 1
          && ga.ga_growsize == (gs < 1 ? 1 : gs), "ga_init");
    // a byte array driven by random appends, compared with a plain buffer
    unsigned char ref[600]; long rlen = 0;
    for (int op = 0; op < 20; op++) {
      long oldmax = ga.ga_maxlen, oldlen = ga.ga_len; unsigned k = rnd() % 4;
      char buf[40]; size_t n = rnd() % 40; for (size_t i = 0; i < n; i++) buf[i] = (char)(rnd() % 3 ? 'a' + rnd() % 3 : 0x80 + rnd() % 128);
      if (rlen + 40 >= (long)sizeof ref) break;
      if (k == 0) { ga_concat_len(&ga, buf, n); memcpy(ref + rlen, buf, n); rlen += (long)n; }
      else if (k == 1) { buf[n] = 0; for (size_t i = 0; i < n; i++) if (!buf[i]) buf[i] = 'q';
        ga_concat(&ga, rnd() % 5 ? buf : NULL); if (ga.ga_len != oldlen) { memcpy(ref + rlen, buf, n); rlen += (long)n; } }
      else if (k == 2) { unsigned char c = (unsigned char)rnd(); ga_append(&ga, c); ref[rlen++] = c; }
      else { int g = (int)(rnd() % 30); ga_grow(&ga, g);
        long want = oldmax - oldlen >= g ? oldmax : oldlen + imax(imax(g, ga.ga_growsize), oldlen / 2);
        CHECK(ga.ga_maxlen == want, "ga_grow maxlen");
        for (long i = oldmax; i < ga.ga_maxlen; i++) CHECK(((char *)ga.ga_data)[i] == 0, "ga_grow zero"); }
      CHECK(ga.ga_len == rlen && (rlen == 0 || !memcmp(ga.ga_data, ref, (size_t)rlen)), "byte array contents");
      if (k != 3 && ga.ga_len > oldlen) {
        long n2 = ga.ga_len - oldlen;
        long want = oldmax - oldlen >= n2 ? oldmax : oldlen + imax(imax(n2, ga.ga_growsize), oldlen / 2);
        CHECK(ga.ga_maxlen == want, "append maxlen");
      }
    }
    long f0 = frees; ga_clear(&ga);
    CHECK(ga.ga_data == NULL && ga.ga_len == 0 && ga.ga_maxlen == 0 && frees - f0 <= 1, "ga_clear");
    // items of 12 bytes through ga_append_via_ptr
    ga_init(&ga, 12, (int)(rnd() % 5));
    int items = (int)(rnd() % 30);
    for (int i = 0; i < items; i++) {
      char *p = ga_append_via_ptr(&ga, 12);
      CHECK(p == (char *)ga.ga_data + 12 * i && ga.ga_len == i + 1, "via_ptr address");
      for (int b = 0; b < 12; b++) CHECK(p[b] == 0, "via_ptr zeroed");
      memset(p, i + 1, 12);
    }
    for (int i = 0; i < items; i++) CHECK(((char *)ga.ga_data)[12 * i + 11] == (char)(i + 1), "via_ptr kept");
    ga_clear(&ga);
    // string arrays: concat, remove duplicates, clear
    ga_init(&ga, (int)sizeof(char *), 4);
    int ns = (int)(rnd() % 9); char *ref2[16]; char sep[4] = {0};
    for (int b = 0, sl = (int)(rnd() % 4); b < sl; b++) sep[b] = (char)(',' + rnd() % 3);
    for (int i = 0; i < ns; i++) {
      char t[6] = {0}; int tl = (int)(rnd() % 4); for (int b = 0; b < tl; b++) t[b] = (char)('a' + rnd() % 2);
      ref2[i] = strdup(t); ga_grow(&ga, 1); ((char **)ga.ga_data)[ga.ga_len++] = xstrdup(t);
    }
    { char want[200] = ""; for (int i = 0; i < ns; i++) { if (i) strcat(want, sep); strcat(want, ref2[i]); }
      char *got = ga_concat_strings(&ga, sep); CHECK(!strcmp(got, want), "ga_concat_strings"); xfree(got); }
    { qsort(ref2, (size_t)ns, sizeof(char *), cmp); int m = 0;
      for (int i = 0; i < ns; i++) if (m == 0 || strcmp(ref2[m - 1], ref2[i])) ref2[m++] = ref2[i]; else free(ref2[i]);
      long f1 = frees; ga_remove_duplicate_strings(&ga);
      CHECK(ga.ga_len == m && frees - f1 == ns - m, "remove_duplicates count");
      for (int i = 0; i < m && i < ga.ga_len; i++) CHECK(!strcmp(((char **)ga.ga_data)[i], ref2[i]), "remove_duplicates order");
      for (int i = 0; i < m; i++) free(ref2[i]);
      long f2 = frees; int had = ga.ga_data != NULL, len = ga.ga_len; ga_clear_strings(&ga);
      CHECK(frees - f2 == len + had && ga.ga_len == 0 && ga.ga_data == NULL, "ga_clear_strings"); }
  }
  printf("%lu checks, %lu mismatches, allocations %ld, frees %ld\n", checks, fails, allocs, frees);
  return fails != 0 || allocs != frees;
}
