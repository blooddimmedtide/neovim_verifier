// Types and constants from memline.c (lines checked by build.py). memchr is CBMC's
// own model of the C library function (trusted).
// CBMC has no memchr model: this is the C standard definition (trusted, listed in PLAN.md).
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#define NUL '\000'
#define FUNC_ATTR_NONNULL_ALL
enum { BLOCK0_ID0 = 'b', BLOCK0_ID1 = '0' };
enum { B0_FNAME_SIZE_ORG = 900, B0_FNAME_SIZE_NOCRYPT = 898, B0_FNAME_SIZE_CRYPT = 890,
       B0_UNAME_SIZE = 40, B0_HNAME_SIZE = 40 };
enum { B0_MAGIC_LONG = 0x30313233, B0_MAGIC_INT = 0x20212223,
       B0_MAGIC_SHORT = 0x10111213, B0_MAGIC_CHAR = 0x55 };
typedef struct {
  char b0_id[2]; char b0_version[10]; char b0_page_size[4]; char b0_mtime[4];
  char b0_ino[4]; char b0_pid[4]; char b0_uname[B0_UNAME_SIZE];
  char b0_hname[B0_HNAME_SIZE]; char b0_fname[B0_FNAME_SIZE_ORG];
  long b0_magic_long; int b0_magic_int; int16_t b0_magic_short; char b0_magic_char;
} ZeroBlock;
void *memchr(const void *s, int c, size_t n) {
  const unsigned char *p = s;
  for (size_t i = 0; i < n; i++) if (p[i] == (unsigned char)c) return (void *)(p + i);
  return NULL;
}
