// Differential test: compiled mpack_core.c (gcc -O2 -fsigned-char) against the
// spec.h references the CBMC proofs use. Exhaustive for every input of up to 3
// bytes; random for 9-byte inputs, tokens, and streams split at random points.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "spec.h"
#include MPACK_CORE_C

static unsigned long fails, cases;
#define CHECK(c, ...) do { cases++; if (!(c)) { if (fails++ < 10) printf(__VA_ARGS__); } } while (0)
static uint64_t rs = 88172645463325252ull;
static uint64_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }

static int same(const mpack_token_t *t, const ref_tok *r) {
  if ((int)t->type != r->type || t->length != r->length) return 0;
  if (r->type <= T_FLOAT) return t->data.value.lo == r->lo && t->data.value.hi == r->hi;
  if (r->type == T_EXT) return t->data.ext_type == r->ext_type;
  return 1;
}

static void one(const uint8_t *b, size_t n) {
  const char *p = (const char *)b; size_t l = n; mpack_token_t t;
  int st = mpack_rtoken(&p, &l, &t);
  ref_tok r; size_t used = 0; uint32_t need = 0;
  int rs_ = ref_decode(b, n, &r, &used, &need);
  CHECK(st == rs_ && (rs_ != R_OK || (same(&t, &r) && l == n - used)) && (rs_ != R_EOF || n == 0 || t.length == need),
        "rtoken %02x len %zu\n", n ? b[0] : 0, n);
}

int main(void) {
  uint8_t b[16];
  for (int n = 0; n <= 3; n++) {
    uint32_t total = 1u << (8 * n);
    for (uint32_t x = 0; x < total; x++) { for (int i = 0; i < n; i++) b[i] = (uint8_t)(x >> (8 * i)); one(b, (size_t)n); }
  }
  for (long k = 0; k < 20000000; k++) { for (int i = 0; i < 9; i++) b[i] = (uint8_t)rnd(); one(b, 9); }
  // Write a random token stream with random buffer splits; read it back with
  // other random splits; compare with the tokens and the reference encoding.
  for (long k = 0; k < 2000000; k++) {
    mpack_token_t toks[8]; ref_tok ks[8]; uint8_t want[512]; int wl = 0; int nt = 1 + (int)(rnd() % 8);
    for (int j = 0; j < nt; j++) {
      int ty; do ty = 1 + (int)(rnd() % 11); while (ty == T_CHUNK);
      mpack_token_t *t = &toks[j]; ref_tok *kk = &ks[j];
      uint32_t len = (uint32_t)rnd(); len >>= rnd() % 33 == 32 ? 0 : (rnd() % 32);
      if (ty >= T_BIN) len %= 24;   // its payload follows in the stream
      t->type = (mpack_token_type_t)ty; t->length = len; *kk = (ref_tok){ty, len, 0, 0, 0};
      if (ty == T_EXT) { t->data.ext_type = (int)(rnd() % 128); kk->ext_type = t->data.ext_type; }
      else if (ty <= T_FLOAT) {
        uint64_t v = rnd() >> (rnd() % 64);
        if (ty == T_SINT) v = (uint64_t)-(int64_t)(v | 1) | 0x8000000000000000ull * (v >> 63 == 0 && rnd() % 2 == 0 ? 0 : 0);
        if (ty == T_SINT && (int64_t)v >= 0) v = ~v;
        if (ty == T_FLOAT) { t->length = kk->length = (rnd() & 1) ? 4 : 8; if (t->length == 4) v &= 0xffffffffu; }
        t->data.value.lo = kk->lo = (uint32_t)v; t->data.value.hi = kk->hi = (uint32_t)(v >> 32);
      }
      wl += ref_encode(kk, want + wl);
      if (ty >= T_BIN) for (uint32_t q = 0; q < len; q++) want[wl++] = (uint8_t)rnd();
    }
    char out[512]; char *o = out; mpack_tokbuf_t wt = MPACK_TOKBUF_INITIAL_VALUE;
    size_t at = 0;   // position in want of the next token's header
    for (int j = 0; j < nt; j++) {
      int st;
      do { size_t room = 1 + rnd() % 10, ol = room; st = mpack_write(&wt, &o, &ol, &toks[j]); } while (st == MPACK_EOF);
      CHECK(st == MPACK_OK, "write status\n");
      uint8_t tmp[16]; at += (size_t)ref_encode(&ks[j], tmp);
      if (ks[j].type >= T_BIN && ks[j].length) {
        mpack_token_t c; c.type = MPACK_TOKEN_CHUNK; c.length = ks[j].length; c.data.chunk_ptr = (const char *)want + at;
        do { size_t room = 1 + rnd() % 10, ol = room; st = mpack_write(&wt, &o, &ol, &c); } while (st == MPACK_EOF);
        CHECK(st == MPACK_OK, "chunk write status\n");
        at += ks[j].length;
      }
    }
    CHECK(o - out == wl && memcmp(out, want, (size_t)wl) == 0, "stream bytes\n");
    mpack_tokbuf_t rt = MPACK_TOKBUF_INITIAL_VALUE; const char *p = out; size_t left = (size_t)wl; int j = 0;
    uint32_t payload = 0;
    while (left) {
      size_t take = 1 + rnd() % 10; if (take > left) take = left;
      size_t l = take; mpack_token_t t;
      int st = mpack_read(&rt, &p, &l, &t);
      left -= take - l;
      if (st == MPACK_EOF) continue;
      CHECK(st == MPACK_OK, "read status\n");
      if (t.type == MPACK_TOKEN_CHUNK) {
        CHECK(t.length <= payload && t.data.chunk_ptr >= out && t.data.chunk_ptr + t.length <= out + wl, "chunk\n");
        payload -= t.length; continue;
      }
      CHECK(payload == 0 && j < nt, "token where payload expected\n");
      if (j >= nt) break;
      ref_tok r; size_t used; uint32_t need;
      uint8_t one_[16]; int ol = ref_encode(&ks[j], one_);
      ref_decode(one_, (size_t)ol, &r, &used, &need);
      CHECK(same(&t, &r), "stream token %d\n", j);
      if (r.type >= T_BIN) payload = r.length;
      j++;
    }
    CHECK(j == nt && left == 0, "all tokens read\n");
  }
  printf("%lu checks, %lu mismatches\n", cases, fails);
  return fails != 0;
}
