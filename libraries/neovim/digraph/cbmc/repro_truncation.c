// Reproducer: registerdigraph() keeps only the low byte of each digraph character.
// digraph_set('ŀx', 'Y') (U+0140) registers '@x' instead; looking up 'ŀx' then fails.
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#define NUL '\000'
#define ESC '\033'
#define IS_SPECIAL(c) ((c) < 0)
#define N_(s) s
#define _(s) s
#define MB_MAXCHAR 6
typedef int result_T;
typedef struct { uint8_t char1; uint8_t char2; result_T result; } digr_T;
typedef struct { int ga_len; int ga_maxlen; int ga_itemsize; int ga_growsize; void *ga_data; } garray_T;
static const char e_digraph_must_be_just_two_characters_str[] = "E1214";
static garray_T user_digraphs = { 0, 0, (int)sizeof(digr_T), 10, NULL };
static void semsg(const char *f, const char *a) { (void)f; (void)a; }
static void emsg(const char *f) { (void)f; }
static int utf_char2bytes(int c, char *buf) { (void)c; buf[0] = 'x'; return 1; }
static void *ga_append_via_ptr(garray_T *gap, size_t sz) {
  gap->ga_data = realloc(gap->ga_data, sz * (size_t)(gap->ga_len + 1));
  return (char *)gap->ga_data + sz * (size_t)gap->ga_len++;
}
#define GA_APPEND_VIA_PTR(item_type, gap) ga_append_via_ptr(gap, sizeof(item_type))
#include "extracted.c"
int main(void) {
  registerdigraph(0x140, 'x', 'Y');
  printf("digraph_get(U+0140,'x') = %d (want %d)\n", digraph_get(0x140, 'x', false), 'Y');
  printf("digraph_get('@','x')    = %d (want %d, unrelated pair)\n", digraph_get('@', 'x', false), 'x');
  return digraph_get(0x140, 'x', false) == 'Y' ? 0 : 1;
}
