// Specs from the doc comments: ml_check_b0_id = "the IDs in b0 are valid" (bytes 'b','0');
// b0_magic_wrong = nonzero iff any byte-order check value differs from what this build
// writes (memline.c ml_open: magic_long/int/short/char assignments); ml_check_b0_strings =
// "all strings in b0 are nul-terminated": a NUL within version[10], uname[40], hname[40]
// and the first 890 bytes of fname (B0_FNAME_SIZE_CRYPT: the rest is used for flags).
#include <assert.h>
static bool has_nul(const char *s, int n) { for (int i = 0; i < n; i++) if (s[i] == 0) return true; return false; }
int main(void) {
  ZeroBlock zb;                 // nondeterministic contents; exact size, so any overread fails
  ZeroBlock *b = &zb;
  assert(ml_check_b0_id(b) == (b->b0_id[0] == 'b' && b->b0_id[1] == '0'));
  bool same = b->b0_magic_long == 0x30313233 && b->b0_magic_int == 0x20212223
              && b->b0_magic_short == 0x1213 && b->b0_magic_char == 0x55;
  assert((b0_magic_wrong(b) != 0) == !same);
  bool ok = has_nul(b->b0_version, 10) && has_nul(b->b0_uname, 40)
            && has_nul(b->b0_hname, 40) && has_nul(b->b0_fname, 890);
  assert(ml_check_b0_strings(b) == ok);
  return 0;
}
