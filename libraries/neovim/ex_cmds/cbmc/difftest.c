// Compiled sub_parse_flags (gcc -O2 -fsigned-char) against spec.h: every string of length <= 5
// over the flag letters plus '&', 'x' and 0xe9, every starting flag state and 'gdefault'.
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#define NUL '\0'
typedef enum { kSubHonorOptions = 0, kSubIgnoreCase, kSubMatchCase } SubIgnoreType;
typedef struct { bool do_all, do_ask, do_count, do_error, do_print, do_list, do_number;
                 SubIgnoreType do_ic; } subflags_T;
enum { RE_SEARCH = 0, RE_SUBST = 1, RE_LAST = 2, RE_BOTH = 3 };
bool p_gd;
#include SUB_C
#include "spec.h"
static const char A[] = "gcnerp#liI&x\xe9";
int main(void)
{
  long n = 0, bad = 0; char s[6]; int na = (int)strlen(A);
  for (int len = 0; len <= 5; len++) {
    long tot = 1; for (int i = 0; i < len; i++) tot *= na;
    for (long k = 0; k < tot; k++) {
      long v = k; for (int i = 0; i < len; i++) { s[i] = A[v % na]; v /= na; } s[len] = 0;
      for (int st = 0; st < 128 * 3 * 2; st++) {
        p_gd = st & 1; int b = st >> 1;
        subflags_T f = { b & 1, b >> 1 & 1, b >> 2 & 1, b >> 3 & 1, b >> 4 & 1, b >> 5 & 1,
                         b >> 6 & 1, (SubIgnoreType)((st >> 8) % 3) };
        ref_flags r = { f.do_all, f.do_ask, f.do_count, f.do_error, f.do_print, f.do_list,
                        f.do_number, (int)f.do_ic };
        int w = 1, rw = 1;
        char *e = sub_parse_flags(s, &f, &w);
        const char *re = ref_parse(s, &r, &rw, p_gd, RE_LAST, 0, 1, 2);
        n++;
        if (e != re || w != rw || f.do_all != r.all || f.do_ask != r.ask || f.do_count != r.count
            || f.do_error != r.error || f.do_print != r.print || f.do_list != r.list
            || f.do_number != r.number || (int)f.do_ic != r.ic) { if (bad++ < 5) printf("diff on \"%s\"\n", s); }
      }
    }
  }
  printf("%ld cases, %ld differences\n", n, bad); return bad != 0;
}
