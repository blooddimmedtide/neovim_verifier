// CBMC harnesses: full functional contracts of the undo-file byte helpers.
// UNDO_IO_C names the file build.py wrote (verbatim upstream pieces after model.h).
#include UNDO_IO_C
#include "spec.h"

uint8_t nondet_u8(void); size_t nondet_size(void); uintmax_t nondet_umax(void);
int nondet_int(void); int64_t nondet_i64(void);

#define MAXIN 33
static uint8_t inbuf[MAXIN];
// A stream holding `len` nondeterministic bytes (len <= MAXIN).
static FILE *stream(size_t len) {
  static FILE f;
  for (size_t i = 0; i < MAXIN; i++) inbuf[i] = nondet_u8();
  f.in = inbuf; f.in_len = len; f.in_pos = 0; f.eof = false; f.out_len = 0;
  f.tell_fails = nondet_bool();
  return &f;
}
static bufinfo_T bi_for(FILE *f) { bufinfo_T bi = { NULL, f, 0 }; return bi; }

// undo_write_bytes: on success writes exactly len bytes, nr mod 256^len, MSB first.
// Precondition: 1 <= len <= 8 (asserted len > 0; the local buffer holds 8). Callers pass 1, 2, 4, 8.
void h_write_bytes(void) {
  size_t len = nondet_size(); uintmax_t nr = nondet_umax();
  if (len < 1 || len > 8) return;
  FILE *f = stream(0); bufinfo_T bi = bi_for(f);
  bool ok = undo_write_bytes(&bi, nr, len);
  if (ok) {
    assert(f->out_len == len);
    assert(be_value(f->out, 0, len) == (u128)nr % pow256(len));
  } else {
    assert(f->out_len == 0);
  }
}

// put_header_ptr: writes the header's sequence number (0 for NULL) in 4 bytes.
void h_put_header_ptr(void) {
  u_header_T h; h.uh_seq = nondet_int();
  bool null = nondet_bool();
  if (!null && h.uh_seq < 0) return;   // asserted by the function
  FILE *f = stream(0); bufinfo_T bi = bi_for(f); writes_may_fail = false;
  put_header_ptr(&bi, null ? NULL : &h);
  assert(f->out_len == 4);
  assert(be_value(f->out, 0, 4) == (u128)(null ? 0 : h.uh_seq));
}

// get4c via undo_read_4c: 4 bytes MSB first as a 32-bit two's complement int, or -1 at EOF.
void h_read_4c(void) {
  size_t len = nondet_size(); if (len > 6) return;
  FILE *f = stream(len); bufinfo_T bi = bi_for(f);
  int r = undo_read_4c(&bi);
  assert((i128)r == spec_4c(inbuf, len, 0));
  assert(f->in_pos == (len >= 4 ? 4 : len));
}

// get2c via undo_read_2c: 2 bytes MSB first (0 .. 65535), or -1 at EOF.
void h_read_2c(void) {
  size_t len = nondet_size(); if (len > 3) return;
  FILE *f = stream(len); bufinfo_T bi = bi_for(f);
  int r = undo_read_2c(&bi);
  assert((i128)r == (len >= 2 ? (i128)be_value(inbuf, 0, 2) : -1));
  assert(f->in_pos == (len >= 2 ? 2 : len));
}

// undo_read_byte: the next byte (0 .. 255), or EOF.
void h_read_byte(void) {
  size_t len = nondet_size(); if (len > 2) return;
  FILE *f = stream(len); bufinfo_T bi = bi_for(f);
  int r = undo_read_byte(&bi);
  assert(r == (len >= 1 ? (int)inbuf[0] : EOF));
}

// get8ctime via undo_read_time: 8 bytes MSB first as a 64-bit two's complement time_t, or -1.
void h_read_time(void) {
  size_t len = nondet_size(); if (len > 9) return;
  FILE *f = stream(len); bufinfo_T bi = bi_for(f);
  time_t r = undo_read_time(&bi);
  assert((i128)r == (len >= 8 ? as_signed(be_value(inbuf, 0, 8), 8) : -1));
}

// undo_read_len: the 4-byte field if it is >= 0 and (when the file size is known) no larger than
// the bytes left after it; otherwise -1 with exactly one corruption report.
void h_read_len(void) {
  size_t len = nondet_size(); if (len > 6) return;
  FILE *f = stream(len); bufinfo_T bi = bi_for(f); bi.bi_fsize = nondet_i64();
  corruption_calls = 0;
  int r = undo_read_len(&bi, "what", "file");
  i128 v = spec_4c(inbuf, len, 0);
  i128 pos = f->tell_fails ? -1 : (i128)(len >= 4 ? 4 : len);
  bool valid = v >= 0 && !(bi.bi_fsize > 0 && (pos < 0 || v > (i128)bi.bi_fsize - pos));
  assert(r == (valid ? (int)v : -1));
  assert(corruption_calls == (valid ? 0 : 1));
  // the message names the field, or says "truncated" when the field itself was cut off
  if (!valid) assert(strcmp(corruption_mesg, len < 4 ? "truncated" : "what") == 0);
}

// undo_read: true and buffer = next size bytes when that many are left; otherwise false and
// the buffer is all zeros.
void h_read(void) {
  size_t len = nondet_size(), size = nondet_size(); if (len > 5 || size > 5) return;
  FILE *f = stream(len); bufinfo_T bi = bi_for(f);
  uint8_t *buf = malloc(size);
  bool ok = undo_read(&bi, buf, size);
  assert(ok == (size > 0 && len >= size));
  for (size_t k = 0; k < size; k++) assert(buf[k] == (ok ? inbuf[k] : 0));
  free(buf);
}

// undo_read_string: NULL when fewer than len bytes are left; otherwise a len+1 block holding
// the next len bytes and a NUL. Nothing leaks (CBMC --memory-leak-check).
void h_read_string(void) {
  size_t len = nondet_size(), have = nondet_size(); if (len > 4 || have > 5) return;
  FILE *f = stream(have); bufinfo_T bi = bi_for(f);
  char *p = undo_read_string(&bi, len);
  if (have >= len) {
    assert(p != NULL);
    for (size_t k = 0; k < len; k++) assert((uint8_t)p[k] == inbuf[k]);
    assert(p[len] == 0);
    free(p);
  } else {
    assert(p == NULL);
  }
}

static void check_pos_bytes(const uint8_t *out, size_t off, pos_T p) {
  assert(be_value(out, off, 4) == (u128)(uint32_t)p.lnum);
  assert(be_value(out, off + 4, 4) == (u128)(uint32_t)p.col);
  assert(be_value(out, off + 8, 4) == (u128)(uint32_t)p.coladd);
}

// serialize_pos: lnum, col, coladd as 4-byte fields (the low 32 bits of each value).
void h_serialize_pos(void) {
  pos_T p = { nondet_int(), nondet_int(), nondet_int() };
  FILE *f = stream(0); bufinfo_T bi = bi_for(f); writes_may_fail = false;
  serialize_pos(&bi, p);
  assert(f->out_len == 12);
  check_pos_bytes(f->out, 0, p);
}

// serialize_visualinfo: start, end, then vi_mode and vi_curswant as 4-byte fields.
void h_serialize_visualinfo(void) {
  visualinfo_T v = { { nondet_int(), nondet_int(), nondet_int() },
                     { nondet_int(), nondet_int(), nondet_int() }, nondet_int(), nondet_int() };
  FILE *f = stream(0); bufinfo_T bi = bi_for(f); writes_may_fail = false;
  serialize_visualinfo(&bi, &v);
  assert(f->out_len == 32);
  check_pos_bytes(f->out, 0, v.vi_start);
  check_pos_bytes(f->out, 12, v.vi_end);
  assert(be_value(f->out, 24, 4) == (u128)(uint32_t)v.vi_mode);
  assert(be_value(f->out, 28, 4) == (u128)(uint32_t)v.vi_curswant);
}

static i128 clamp0(i128 x) { return x < 0 ? 0 : x; }

// unserialize_pos: three 4-byte fields, each negative value (or EOF) replaced by 0.
void h_unserialize_pos(void) {
  size_t len = nondet_size(); if (len > 13) return;
  FILE *f = stream(len); bufinfo_T bi = bi_for(f);
  pos_T p; unserialize_pos(&bi, &p);
  assert(p.lnum == clamp0(spec_4c(inbuf, len, 0)));
  assert(p.col == clamp0(spec_4c(inbuf, len, 4)));
  assert(p.coladd == clamp0(spec_4c(inbuf, len, 8)));
}

// unserialize_visualinfo: two clamped positions, then vi_mode and vi_curswant as read (-1 at EOF).
void h_unserialize_visualinfo(void) {
  size_t len = nondet_size(); if (len > MAXIN) return;   // fields end at byte 32: EOF in every field
  FILE *f = stream(len); bufinfo_T bi = bi_for(f);
  visualinfo_T v; unserialize_visualinfo(&bi, &v);
  assert(v.vi_start.lnum == clamp0(spec_4c(inbuf, len, 0)));
  assert(v.vi_start.col == clamp0(spec_4c(inbuf, len, 4)));
  assert(v.vi_start.coladd == clamp0(spec_4c(inbuf, len, 8)));
  assert(v.vi_end.lnum == clamp0(spec_4c(inbuf, len, 12)));
  assert(v.vi_end.col == clamp0(spec_4c(inbuf, len, 16)));
  assert(v.vi_end.coladd == clamp0(spec_4c(inbuf, len, 20)));
  assert(v.vi_mode == spec_4c(inbuf, len, 24));
  assert(v.vi_curswant == spec_4c(inbuf, len, 28));
}

// uhp_seq_cmp: -1, 0, 1 as the first header's uh_seq is below, equal to, above the second's.
void h_seq_cmp(void) {
  u_header_T a, b; a.uh_seq = nondet_int(); b.uh_seq = nondet_int();
  u_header_T *pa = &a, *pb = &b;
  int r = uhp_seq_cmp(&pa, &pb);
  assert(r == (a.uh_seq < b.uh_seq ? -1 : a.uh_seq == b.uh_seq ? 0 : 1));
}

// uhp_table_find (bounded: num_head <= TABLE_MAX; the unbounded proof is the WP one):
// on a table sorted on uh_seq, returns an index holding seq, or -1 when no entry holds it.
#ifndef TABLE_MAX
#define TABLE_MAX 4
#endif
void h_table_find(void) {
  int n = nondet_int(); if (n > TABLE_MAX) return;   // n <= 0 allowed: empty table
  u_header_T hs[TABLE_MAX]; u_header_T *tab[TABLE_MAX];
  for (int i = 0; i < TABLE_MAX; i++) { hs[i].uh_seq = nondet_int(); tab[i] = &hs[i]; }
  for (int i = 0; i + 1 < n; i++) if (hs[i].uh_seq > hs[i + 1].uh_seq) return;   // sorted
  int seq = nondet_int();
  int r = uhp_table_find(tab, n, seq);
  bool present = false;
  for (int i = 0; i < n; i++) if (hs[i].uh_seq == seq) present = true;
  if (present) { assert(0 <= r && r < n); assert(hs[r].uh_seq == seq); }
  else assert(r == -1);
}

// Unbounded versions: any stream length and any size (below 2^40, more than any undo file
// field; undo_read_len limits lengths to int). No loop: one nondeterministic index k stands for
// every index, so the property holds for all of them.
void h_read_any(void) {
  size_t len = nondet_size(), size = nondet_size();
  if (len >= ((size_t)1 << 40) || size >= ((size_t)1 << 40)) return;
  uint8_t *in = malloc(len);
  static FILE f; f.in = in; f.in_len = len; f.in_pos = 0; f.eof = false; f.out_len = 0;
  bufinfo_T bi = bi_for(&f);
  uint8_t *buf = malloc(size);
  size_t k = nondet_size();
  uint8_t ink = k < len ? in[k] : 0;
  bool ok = undo_read(&bi, buf, size);
  assert(ok == (size > 0 && len >= size));
  if (k < size) assert(buf[k] == (ok ? ink : 0));
  free(buf); free(in);
}

void h_read_string_any(void) {
  size_t len = nondet_size(), have = nondet_size();
  if (len >= ((size_t)1 << 40) || have >= ((size_t)1 << 40)) return;
  uint8_t *in = malloc(have);
  static FILE f; f.in = in; f.in_len = have; f.in_pos = 0; f.eof = false; f.out_len = 0;
  bufinfo_T bi = bi_for(&f);
  size_t k = nondet_size();
  uint8_t ink = k < have ? in[k] : 0;
  char *p = undo_read_string(&bi, len);
  if (have >= len) {
    assert(p != NULL);
    if (k < len) assert((uint8_t)p[k] == ink);
    assert(p[len] == 0);
    free(p);
  } else {
    assert(p == NULL);
  }
  free(in);
}
