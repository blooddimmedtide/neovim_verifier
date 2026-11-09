// serialize_extmark: for a splice or move, writes the 2-byte entry magic 0xf518, the type in 4
// bytes, then the struct's bytes as they are in memory; returns false only when the struct write
// fails. Other types: writes nothing, returns true.
// unserialize_extmark: reads a 4-byte type; for splice/move then the struct's bytes. Returns a
// new object with that type and those bytes, or NULL with *error set when the type is anything
// else or the bytes are cut off. Nothing leaks either way.
#define OUT_CAP 64
#include UNDO_IO_C
#include "spec.h"
uint8_t nondet_u8(void); size_t nondet_size(void); int nondet_int(void);
#define MAXIN (4 + sizeof(ExtmarkSplice) + 1)
static uint8_t inbuf[MAXIN];

void h_serialize_extmark(void) {
  ExtmarkUndoObject x; uint8_t *raw = (uint8_t *)&x;
  for (size_t i = 0; i < sizeof x; i++) raw[i] = nondet_u8();
  x.type = (UndoObjectType)nondet_int();
  static FILE f; f.in_len = 0; f.out_len = 0; f.eof = false;
  bufinfo_T bi = { NULL, &f, 0 };
  bool ok = serialize_extmark(&bi, x);
  if (x.type == kExtmarkSplice || x.type == kExtmarkMove) {
    size_t n = x.type == kExtmarkSplice ? sizeof(ExtmarkSplice) : sizeof(ExtmarkMove);
    const uint8_t *src = (const uint8_t *)&x.data;
    // the two header writes may each fail (nondet); the struct write decides the result
    if (ok) {
      assert(f.out_len >= n);
      for (size_t k = 0; k < n; k++) assert(f.out[f.out_len - n + k] == src[k]);
      if (f.out_len == 6 + n) {
        assert(be_value(f.out, 0, 2) == 0xf518);
        assert(be_value(f.out, 2, 4) == (u128)(uint32_t)x.type);
      }
    }
  } else {
    assert(ok && f.out_len == 0);
  }
}

void h_serialize_extmark_ok(void) {   // all writes succeed: exact byte image
  ExtmarkUndoObject x; uint8_t *raw = (uint8_t *)&x;
  for (size_t i = 0; i < sizeof x; i++) raw[i] = nondet_u8();
  x.type = nondet_bool() ? kExtmarkSplice : kExtmarkMove;
  static FILE f; f.in_len = 0; f.out_len = 0; f.eof = false; writes_may_fail = false;
  bufinfo_T bi = { NULL, &f, 0 };
  assert(serialize_extmark(&bi, x));
  size_t n = x.type == kExtmarkSplice ? sizeof(ExtmarkSplice) : sizeof(ExtmarkMove);
  assert(f.out_len == 6 + n);
  assert(be_value(f.out, 0, 2) == 0xf518);
  assert(be_value(f.out, 2, 4) == (u128)(uint32_t)x.type);
  const uint8_t *src = (const uint8_t *)&x.data;
  for (size_t k = 0; k < n; k++) assert(f.out[6 + k] == src[k]);
}

void h_unserialize_extmark(void) {
  size_t len = nondet_size(); if (len > MAXIN) return;
  for (size_t i = 0; i < MAXIN; i++) inbuf[i] = nondet_u8();
  static FILE f; f.in = inbuf; f.in_len = len; f.in_pos = 0; f.eof = false;
  bufinfo_T bi = { NULL, &f, 0 };
  bool error = false;
  ExtmarkUndoObject *r = unserialize_extmark(&bi, &error, "file");
  i128 t = spec_4c(inbuf, len, 0);
  size_t n = t == kExtmarkSplice ? sizeof(ExtmarkSplice) : t == kExtmarkMove ? sizeof(ExtmarkMove) : 0;
  bool good = n > 0 && len >= 4 + n;
  if (good) {
    assert(r != NULL && !error && (i128)r->type == t);
    const uint8_t *got = (const uint8_t *)&r->data;
    for (size_t k = 0; k < n; k++) assert(got[k] == inbuf[4 + k]);
    free(r);
  } else {
    assert(r == NULL && error);
  }
}
