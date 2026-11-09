// C standard string functions the copied code calls, written as the C standard
// (C11 7.24) describes them, so CBMC checks each byte they read. They replace
// CBMC's built-in models.
#define strchr  nv_strchr
#define strstr  nv_strstr
#define strncmp nv_strncmp
#define strlen  nv_strlen
static size_t nv_strlen(const char *s) { size_t i = 0; while (s[i] != 0) i++; return i; }
static char *nv_strchr(const char *s, int c)
{ for (;; s++) { if (*s == (char)c) return (char *)s; if (*s == 0) return 0; } }
static int nv_strncmp(const char *a, const char *b, size_t n)
{ for (size_t i = 0; i < n; i++) { unsigned char x = (unsigned char)a[i], y = (unsigned char)b[i];
    if (x != y) return x < y ? -1 : 1; if (x == 0) return 0; } return 0; }
static char *nv_strstr(const char *h, const char *nd) { assert(0 && "unreachable"); return 0; }
