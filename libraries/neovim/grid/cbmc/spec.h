// Independent reference, written from the meaning of schar_T (grid.c header comment, types_defs.h):
// a schar_T is 4 bytes in memory. If byte 0 is 0xFF (never a UTF-8 byte) the other 3 bytes are a
// little-endian byte offset into glyph_cache.keys; otherwise the bytes are the glyph's UTF-8 text,
// NUL padded (no NUL inside).
static void bytes_of(schar_T sc, unsigned char b[4]) { memcpy(b, &sc, 4); }
static bool ref_high(schar_T sc) { unsigned char b[4]; bytes_of(sc, b); return b[0] == 0xFF; }
static uint32_t ref_idx(schar_T sc) {
  unsigned char b[4]; bytes_of(sc, b); return b[1] | ((uint32_t)b[2] << 8) | ((uint32_t)b[3] << 16);
}
// The glyph's text: pointer and length.
static const char *ref_text(schar_T sc, size_t *len, char tmp[5]) {
  if (ref_high(sc)) {
    const char *p = &glyph_cache.keys[ref_idx(sc)]; size_t n = 0;
    while (p[n] != 0) n++;
    *len = n; return p;
  }
  memcpy(tmp, &sc, 4); tmp[4] = 0; size_t n = 0;
  while (n < 4 && tmp[n] != 0) n++;
  *len = n; return tmp;
}
// UTF-8 (RFC 3629 bit layout, extended to 21 bits as Neovim does) of 0 <= c < 0x200000.
static size_t ref_utf8(int c, unsigned char out[4]) {
  size_t n = c < 0x80 ? 1 : c < 0x800 ? 2 : c < 0x10000 ? 3 : 4;
  static const unsigned char lead[5] = { 0, 0x00, 0xC0, 0xE0, 0xF0 };
  unsigned v = (unsigned)c;
  for (size_t i = n - 1; i > 0; i--) { out[i] = (unsigned char)(0x80 | (v % 64)); v /= 64; }
  out[0] = (unsigned char)(lead[n] | v);
  return n;
}
