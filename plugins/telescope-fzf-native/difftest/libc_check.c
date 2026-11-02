// Checks ../cbmc/libc_model.c (the C-library models the CBMC proofs use)
// against glibc in the "C" locale: every byte for isspace/tolower, random
// strings for the string functions. Exit 0 = all agree.
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#undef isspace   // glibc macros; the functions are compared below
#undef tolower
#define isspace m_isspace
#define tolower m_tolower
#define strtok m_strtok
#define strstr m_strstr
#define memset m_memset
#define strlen m_strlen
#define strncmp m_strncmp
#define strcmp m_strcmp
#define strchr m_strchr
#define strcpy m_strcpy
#define strncpy m_strncpy
#define strdup m_strdup
#include "libc_model.c"
#undef isspace
#undef tolower
#undef strtok
#undef strstr
#undef memset
#undef strlen
#undef strncmp
#undef strcmp
#undef strchr
#undef strcpy
#undef strncpy
#undef strdup
static unsigned long long s = 99;
static unsigned r(unsigned n) { s ^= s << 13; s ^= s >> 7; s ^= s << 17; return (unsigned)(s % n); }
static int sgn(int x) { return (x > 0) - (x < 0); }
#define FAIL(...) do { printf(__VA_ARGS__); printf("\n"); return 1; } while (0)
static void gen(char *b, int n) { const char a[] = "ab \t\\x"; for (int i = 0; i < n; i++) b[i] = r(8) ? a[r(6)] : (char)(1 + r(255)); b[n] = 0; }
int main(void) {
  for (int c = -1; c < 256; c++) {
    if (!!isspace(c) != !!m_isspace(c)) FAIL("isspace %d", c);
    if (tolower(c) != m_tolower(c)) FAIL("tolower %d", c);
  }
  char a[40], b[40], c1[40], c2[40];
  for (long it = 0; it < 2000000; it++) {
    int n = r(12), m = r(4);
    gen(a, n); gen(b, m);
    if (strlen(a) != m_strlen(a)) FAIL("strlen");
    size_t k = r(15);
    if (sgn(strncmp(a, b, k)) != sgn(m_strncmp(a, b, k))) FAIL("strncmp");
    if (sgn(strcmp(a, b)) != sgn(m_strcmp(a, b))) FAIL("strcmp");
    int ch = r(4) ? a[r(n + 1)] : (int)r(256);
    if (strchr(a, ch) != m_strchr(a, ch)) FAIL("strchr");
    if (strstr(a, b) != m_strstr(a, b)) FAIL("strstr");
    memset(c1, 'z', 40); memset(c2, 'z', 40);
    strcpy(c1, a); m_strcpy(c2, a); if (memcmp(c1, c2, 40)) FAIL("strcpy");
    strncpy(c1, a, k); m_strncpy(c2, a, k); if (memcmp(c1, c2, 40)) FAIL("strncpy");
    m_memset(c2, ch, k); memset(c1, ch, k); if (memcmp(c1, c2, 40)) FAIL("memset");
    char *d1 = strdup(a), *d2 = m_strdup(a); if (strcmp(d1, d2)) FAIL("strdup"); free(d1); free(d2);
    // strtok over the whole sequence of calls
    strcpy(c1, a); strcpy(c2, a);
    char *t1 = strtok(c1, " "), *t2 = m_strtok(c2, " ");
    for (;;) {
      if ((t1 == NULL) != (t2 == NULL)) FAIL("strtok null");
      if (!t1) break;
      if (t1 - c1 != t2 - c2 || strcmp(t1, t2)) FAIL("strtok token");
      t1 = strtok(NULL, " "); t2 = m_strtok(NULL, " ");
    }
    if (memcmp(c1, c2, n + 1)) FAIL("strtok buffer");
  }
  printf("libc models agree with glibc (C locale): isspace/tolower on -1..255, 2000000 random string cases\n");
  return 0;
}
