// CBMC harness: add_char2buf and special_to_buf (verbatim) with the verbatim
// utf_char2bytes (mbyte.c, proved separately in ../../mbyte/cbmc) linked in.
// Reference from the doc comments: modifiers become K_SPECIAL KS_MODIFIER mods; a special
// key becomes K_SPECIAL + its two termcap bytes; a character is its UTF-8 bytes, with each
// K_SPECIAL byte written as K_SPECIAL KS_SPECIAL KE_FILLER when escaping.
#include "kc.c"
#include "utf.c"
int nondet_int(void);
_Bool nondet_bool(void);

static int ref_escape(int c, char *out) {   // the escaped encoding of c
  char enc[8];
  int n = utf_char2bytes(c, enc), o = 0;
  for (int i = 0; i < n; i++) {
    if ((uint8_t)enc[i] == 0x80) { out[o++] = (char)0x80; out[o++] = (char)254; out[o++] = 'X'; }
    else out[o++] = enc[i];
  }
  return o;
}

int main(void) {
  int key = nondet_int();
#ifdef ADD_CHAR2BUF
  char buf[18];                      // exact size: 6 bytes, each possibly escaped to 3
  char want[18];
  int wn = ref_escape(key, want);
  char *end = add_char2buf(key, buf);
  __CPROVER_assert(end - buf == wn, "length");
  for (int i = 0; i < wn; i++) __CPROVER_assert(buf[i] == want[i], "bytes");
#else
  int mods = nondet_int(); _Bool esc = nondet_bool();
  __CPROVER_assume(key != INT_MIN);  // findings/keycodes-char-int-min.md
  char dst[21];                      // exact size: 3 modifier bytes + 18
  char want[21]; int wn = 0;
  if (mods != 0) { want[wn++] = (char)0x80; want[wn++] = (char)252; want[wn++] = (char)(uint8_t)mods; }
  if (key < 0) {
    unsigned u = 0u - (unsigned)key;
    want[wn++] = (char)0x80; want[wn++] = (char)(u & 0xff); want[wn++] = (char)((u >> 8) & 0xff);
  } else if (esc) {
    wn += ref_escape(key, want + wn);
  } else {
    wn += utf_char2bytes(key, want + wn);
  }
  unsigned n = special_to_buf(key, mods, esc, dst);
  __CPROVER_assert(n == (unsigned)wn, "length");
  for (int i = 0; i < wn; i++) __CPROVER_assert(dst[i] == want[i], "bytes");
#endif
  return 0;
}
