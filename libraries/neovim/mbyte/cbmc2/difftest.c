// Differential test: compiled code vs ../cbmc/spec.h. Exhaustive over all
// 1-3 byte inputs (plus a 0 terminator), random 4-6 byte inputs.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../cbmc/spec.h"
#include MBYTE_UTF8_C
static long fails;
static void one(const uint8_t *b, int n) {
  char buf[8] = {0}; memcpy(buf, b, (size_t)n);
  if (n && (uint8_t)buf[0] >= 0x80 && memchr(buf, 0, (size_t)n) == NULL) {
    int L = spec_lead_len(b[0]); int ok = L >= 2;
    for (int k = 1; ok && k < L; k++) if (!spec_is_cont((uint8_t)buf[k])) ok = 0;
    int32_t r = utf_ptr2CharInfo_impl((uint8_t *)buf, utf8len_tab[(uint8_t)buf[0]]);
    if (ok ? r != (int32_t)spec_value((uint8_t *)buf, L) : r >= 0) fails++;
  }
  const char *p = buf; int c = mb_cptr2char_adv(&p);
  if (c != ref_ptr2char((uint8_t *)buf) || p != buf + ref_ptr2len((uint8_t *)buf)) fails++;
  const char *s = buf; size_t m = (size_t)n; int r = utf_safe_read_char_adv(&s, &m);
  if (n == 0) { if (r != 0 || s != buf) fails++; return; }
  if (b[0] < 0x80) { if (r != b[0] || s != buf + 1) fails++; return; }
  int L = spec_lead_len(b[0]); int ok = L >= 2 && L <= n;
  for (int k = 1; ok && k < L; k++) if (!spec_is_cont(b[k])) ok = 0;
  if (ok ? (r != (int)spec_value(b, L) || s != buf + L) : (r != -1 || s != buf)) fails++;
}
int main(void) {
  uint8_t b[6]; one(b, 0);
  for (int x = 0; x < 256; x++) { b[0] = x; one(b, 1);
    for (int y = 0; y < 256; y++) { b[1] = y; one(b, 2);
      for (int z = 0; z < 256; z++) { b[2] = z; one(b, 3); } } }
  srand(1);
  for (long i = 0; i < 20000000; i++) { int n = 4 + rand() % 3;
    for (int k = 0; k < n; k++) b[k] = k ? 0x80 | (rand() & 0x3F) ^ (rand() % 16 == 0 ? 0x40 : 0) : 0xC0 | rand(); one(b, n); }
  printf("fails=%ld\n", fails); return fails != 0;
}
