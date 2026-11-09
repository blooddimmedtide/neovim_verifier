// CBMC harnesses for unserialize_uep / serialize_uep. BOUNDED: ue_size <= UEP_MAX lines of
// at most LINE_MAX bytes (the loops depend on file content). Properties: the entry read matches
// the bytes (fields, line count, each line), every error path sets *error with the entry safe to
// free (ue_size counts only allocated lines' slots, and ue_array slots are NULL or lines), no
// leak once the caller frees the entry, and serialize_uep writes exactly the bytes
// unserialize_uep reads back (round trip).
#include UNDO_IO_C
#include "spec.h"
uint8_t nondet_u8(void); size_t nondet_size(void); int nondet_int(void); int64_t nondet_i64(void);
#ifndef UEP_MAX
#define UEP_MAX 2
#endif
#define LINE_MAX_ 2
#define MAXIN (16 + UEP_MAX * (4 + LINE_MAX_) + 1)
static uint8_t inbuf[MAXIN];

// What u_freeentry does with an entry (free each array slot below ue_size, the array, the entry).
static void free_entry(u_entry_T *uep) {
  for (int i = 0; i < uep->ue_size; i++) free(uep->ue_array[i]);
  free(uep->ue_array);
  free(uep);
}

void h_unserialize_uep(void) {
  size_t len = nondet_size(); if (len > MAXIN) return;
  for (size_t i = 0; i < MAXIN; i++) inbuf[i] = nondet_u8();
  // keep the loop bounded: the size field (bytes 12..15) is at most UEP_MAX
  if (len >= 16 && be_value(inbuf, 12, 4) > UEP_MAX) return;
  static FILE f; f.in = inbuf; f.in_len = len; f.in_pos = 0; f.eof = false;
  f.tell_fails = nondet_bool();
  bufinfo_T bi = { NULL, &f, nondet_bool() ? 0 : (off_T)len };
  bool error = false; corruption_calls = 0;
  u_entry_T *uep = unserialize_uep(&bi, &error, "file");
  assert(uep != NULL);
  i128 top = spec_4c(inbuf, len, 0), bot = spec_4c(inbuf, len, 4), lc = spec_4c(inbuf, len, 8);
  if (top < 0 || bot < 0 || lc < 0) {
    assert(error && uep->ue_size == 0 && corruption_calls == 1);
  } else {
    assert(uep->ue_top == top && uep->ue_bot == bot && uep->ue_lcount == lc);
    if (!error) {
      // success: ue_size lines, each a NUL-terminated copy of its bytes, all of the stream used
      size_t off = 16;
      assert((i128)uep->ue_size == spec_4c(inbuf, len, 12));
      for (int i = 0; i < uep->ue_size; i++) {
        i128 l = spec_4c(inbuf, len, off);
        assert(l >= 0 && uep->ue_array[i] != NULL);
        for (i128 k = 0; k < l; k++) assert((uint8_t)uep->ue_array[i][k] == inbuf[off + 4 + k]);
        assert(uep->ue_array[i][l] == 0);
        off += 4 + (size_t)l;
      }
      assert(f.in_pos == off);
    } else {
      assert(uep->ue_size >= 0);
    }
  }
  free_entry(uep);
}

// Round trip: serialize an entry with ue_size <= UEP_MAX short lines, read it back.
void h_uep_roundtrip(void) {
  static char lines[UEP_MAX][LINE_MAX_ + 1]; static char *arr[UEP_MAX];
  u_entry_T e = { NULL, nondet_int(), nondet_int(), nondet_int(), arr, nondet_int() };
  if (e.ue_top < 0 || e.ue_bot < 0 || e.ue_lcount < 0 || e.ue_size < 0 || e.ue_size > UEP_MAX) return;
  for (int i = 0; i < UEP_MAX; i++) {
    for (int k = 0; k < LINE_MAX_; k++) lines[i][k] = (char)nondet_u8();
    lines[i][LINE_MAX_] = 0; arr[i] = lines[i];
  }
  static FILE f; f.in_len = 0; f.out_len = 0; f.eof = false; f.tell_fails = false;
  writes_may_fail = false;
  bufinfo_T bi = { NULL, &f, 0 };
  assert(serialize_uep(&bi, &e));
  // read back what was written
  static FILE g; g.in = f.out; g.in_len = f.out_len; g.in_pos = 0; g.eof = false; g.tell_fails = false;
  bufinfo_T bj = { NULL, &g, (off_T)f.out_len };
  bool error = false;
  u_entry_T *r = unserialize_uep(&bj, &error, "file");
  assert(!error);
  assert(r->ue_top == e.ue_top && r->ue_bot == e.ue_bot && r->ue_lcount == e.ue_lcount);
  assert(r->ue_size == e.ue_size);
  for (int i = 0; i < e.ue_size; i++) assert(strcmp(r->ue_array[i], e.ue_array[i]) == 0);
  assert(g.in_pos == g.in_len);
  free_entry(r);
}
