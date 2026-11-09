// Independent reference, written from the Unicode BOM table (UTF-8 EF BB BF,
// UTF-16/UCS-2 BE FE FF, LE FF FE, UCS-4 BE 00 00 FE FF, LE FF FE 00 00) and
// fileio.c's doc: "Check for a Unicode BOM ... return the name of the encoding
// or NULL; *lenp gets the BOM length; flags restrict what is accepted".
// Decided by the reference: when no BOM matches, len is 2 and result NULL.
#include <stdint.h>
#include <string.h>
enum { FIO_UTF8 = 0x02, FIO_UCS2 = 0x04, FIO_UCS4 = 0x08, FIO_UTF16 = 0x10,
       FIO_ENDIAN_L = 0x80, FIO_ALL = -1 };
static const char *ref_bom(const uint8_t *b, int n, int fl, int *len) {
  int all = fl == FIO_ALL;
  *len = 2;
  if (n >= 3 && b[0] == 0xEF && b[1] == 0xBB && b[2] == 0xBF) {
    if (all || fl == FIO_UTF8 || fl == 0) { *len = 3; return "utf-8"; }
    return 0;
  }
  if (b[0] == 0xFF && b[1] == 0xFE) {
    if (n >= 4 && b[2] == 0 && b[3] == 0 && (all || fl == (FIO_UCS4 | FIO_ENDIAN_L))) {
      *len = 4; return "ucs-4le";
    }
    if (fl == (FIO_UCS2 | FIO_ENDIAN_L)) return "ucs-2le";
    if (all || fl == (FIO_UTF16 | FIO_ENDIAN_L)) return "utf-16le";
    return 0;
  }
  if (b[0] == 0xFE && b[1] == 0xFF) {
    if (fl == FIO_UCS2) return "ucs-2";
    if (all || fl == FIO_UTF16) return "utf-16";
    return 0;
  }
  if (n >= 4 && b[0] == 0 && b[1] == 0 && b[2] == 0xFE && b[3] == 0xFF
      && (all || fl == FIO_UCS4)) { *len = 4; return "ucs-4"; }
  return 0;
}
