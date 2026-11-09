/* Prelude for WP proofs of src/nvim/os/env.c. Contracts here are TRUSTED (C11 libc,
   and xmemrchr, proved in libraries/neovim/memory). Nothing else is assumed. */
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#define NUL '\0'
#define FUNC_ATTR_NONNULL_ARG(...)
#define FUNC_ATTR_WARN_UNUSED_RESULT
/*@ predicate str_len{L}(char *s, integer n) = 0 <= n && \valid_read(s + (0 .. n)) && s[n] == 0
      && \forall integer i; 0 <= i < n ==> s[i] != 0;
    predicate is_str{L}(char *s) = \exists integer n; str_len(s, n); */
/*@ requires is_str((char *)s);
    assigns \nothing;
    ensures str_len((char *)s, \result); */
size_t vp_strlen(const char *s);
/*@ requires is_str((char *)s);
    assigns \nothing;
    ensures \result == \null || \exists integer i; 0 <= i && \result == s + i && s[i] == (char)c
              && \forall integer j; 0 <= j < i ==> s[j] != (char)c && s[j] != 0;
    ensures \result == \null <==> (char)c != 0 && \exists integer n; str_len((char *)s, n)
              && \forall integer j; 0 <= j < n ==> s[j] != (char)c; */
char *vp_strchr(const char *s, int c);
/*@ requires \valid_read((uint8_t *)src + (0 .. len - 1));
    assigns \nothing;
    behavior found:
      assumes \exists integer i; 0 <= i < len && ((uint8_t *)src)[i] == c;
      ensures \exists integer i; 0 <= i < len && (uint8_t *)\result == (uint8_t *)src + i
              && ((uint8_t *)src)[i] == c && \forall integer j; i < j < len ==> ((uint8_t *)src)[j] != c;
    behavior not_found:
      assumes \forall integer i; 0 <= i < len ==> ((uint8_t *)src)[i] != c;
      ensures \result == \null;
    complete behaviors; disjoint behaviors; */
void *xmemrchr(const void *src, uint8_t c, size_t len);
#define strlen vp_strlen
#define strchr vp_strchr
