// CBMC proofs of full functional correctness of src/mpack/mpack_core.c
// (Neovim's MessagePack tokenizer), for every input. The upstream file is
// included unchanged; inputs are nondeterministic and every loop is fully
// unwound (--unwinding-assertions), so each check covers all inputs.
#include <stdint.h>
#include <stdlib.h>
#include "spec.h"
#include MPACK_CORE_C

size_t nondet_size(void);
uint32_t nondet_u32(void);
int nondet_int(void);

static int same_token(const mpack_token_t *t, const ref_tok *r) {
  if ((int)t->type != r->type || t->length != r->length) return 0;
  switch (r->type) {
    case T_NIL: case T_BOOL: case T_UINT: case T_SINT: case T_FLOAT:
      return t->data.value.lo == r->lo && t->data.value.hi == r->hi;
    case T_EXT:
      return t->data.ext_type == r->ext_type;
    default:
      return 1;   // array/map/str/bin carry only the length
  }
}

// An input of n bytes in an object of exactly n bytes (n <= 9, the longest
// header), or 9 bytes with any larger buflen: the pointer check proves no
// read past the header, so longer inputs behave the same.
static const char *any_input(size_t *n) {
  size_t len = nondet_size();
  size_t obj = len < MPACK_MAX_TOKEN_LEN ? len : MPACK_MAX_TOKEN_LEN;
  *n = len;
  return malloc(obj);
}

// mpack_rtoken: the token the spec defines; consumes exactly its header.
void h_rtoken(void) {
  size_t n; const char *in = any_input(&n);
  const char *b = in; size_t bl = n;
  mpack_token_t tok;
  int st = mpack_rtoken(&b, &bl, &tok);
  ref_tok r; size_t used = 0; uint32_t need = 0;
  int rs = ref_decode((const uint8_t *)in, n < 9 ? n : 9, &r, &used, &need);
  __CPROVER_assert(st == rs, "status");
  if (rs == R_OK) {
    __CPROVER_assert(same_token(&tok, &r), "token");
    __CPROVER_assert(b == in + used && bl == n - used, "consumes the header");
  }
  if (rs == R_EOF && n > 0) __CPROVER_assert(tok.length == need, "EOF reports header size - 1");
}

// mpack_wtoken (via the static writer, given the 9 bytes mpack_write always
// provides): writes the shortest encoding, which decodes back to the token.
void h_wtoken(void) {
  mpack_token_t tok;
  int ty = nondet_int();
  __CPROVER_assume(ty >= MPACK_TOKEN_NIL && ty <= MPACK_TOKEN_EXT && ty != MPACK_TOKEN_CHUNK);
  tok.type = (mpack_token_type_t)ty;
  tok.length = nondet_u32();
  ref_tok k = {ty, tok.length, 0, 0, 0};
  if (ty == MPACK_TOKEN_EXT) {
    tok.data.ext_type = nondet_int();
    // mpack_wext asserts 0 <= type < 0x80; lmpack's packer checks the same.
    __CPROVER_assume(tok.data.ext_type >= 0 && tok.data.ext_type < 0x80);
    k.ext_type = tok.data.ext_type;
  } else if (ty <= MPACK_TOKEN_FLOAT) {
    tok.data.value.lo = nondet_u32(); tok.data.value.hi = nondet_u32();
    k.lo = tok.data.value.lo; k.hi = tok.data.value.hi;
    // SINT tokens come from mpack_pack_sint: a negative 64-bit value.
    if (ty == MPACK_TOKEN_SINT) __CPROVER_assume(k.hi >= 0x80000000u);
    // A float is 4 or 8 bytes; a 4-byte float has its bits in lo.
    if (ty == MPACK_TOKEN_FLOAT && tok.length != 4 && tok.length != 8) {
      char out[9]; char *o = out; size_t ol = 9;
      __CPROVER_assert(mpack_wtoken(&tok, &o, &ol) == MPACK_ERROR, "bad float length -> error");
      return;
    }
    if (ty == MPACK_TOKEN_FLOAT && tok.length == 4) __CPROVER_assume(k.hi == 0);
  }
  char out[9]; char *o = out; size_t ol = 9;
  int st = mpack_wtoken(&tok, &o, &ol);
  uint8_t want[9]; int w = ref_encode(&k, want);
  __CPROVER_assert(st == MPACK_OK, "status");
  __CPROVER_assert((size_t)(o - out) == (size_t)w && ol == 9 - (size_t)w, "length");
  for (int i = 0; i < w; i++) __CPROVER_assert((uint8_t)out[i] == want[i], "bytes = shortest encoding");
  // Round trip through the spec decoder: same type and length, same value.
  ref_tok r; size_t used = 0; uint32_t need = 0;
  __CPROVER_assert(ref_decode((const uint8_t *)out, (size_t)w, &r, &used, &need) == R_OK && used == (size_t)w, "decodes");
  if (ty == MPACK_TOKEN_UINT) {
    uint64_t v = ((uint64_t)r.hi << 32) | r.lo;
    __CPROVER_assert(r.type == T_UINT && v == (((uint64_t)k.hi << 32) | k.lo), "uint round trip");
  } else if (ty == MPACK_TOKEN_SINT) {
    // sign-extend the decoded raw bits from their width
    uint64_t raw = r.length == 8 ? (((uint64_t)r.hi << 32) | r.lo) : r.lo;
    int bits = r.length * 8;
    int64_t v = bits == 64 ? (int64_t)raw : (int64_t)(raw << (64 - bits)) >> (64 - bits);
    __CPROVER_assert(r.type == T_SINT && v == (int64_t)(((uint64_t)k.hi << 32) | k.lo), "sint round trip");
  } else if (ty == MPACK_TOKEN_BOOLEAN) {
    __CPROVER_assert(r.type == T_BOOL && r.lo == (k.lo != 0), "bool round trip");
  } else {
    __CPROVER_assert(r.type == ty && (ty == MPACK_TOKEN_NIL || r.length == k.length), "type and length");
    if (ty == MPACK_TOKEN_FLOAT) __CPROVER_assert(r.lo == k.lo && r.hi == k.hi, "float bits");
    if (ty == MPACK_TOKEN_EXT) __CPROVER_assert(r.ext_type == k.ext_type, "ext type");
  }
}

// ---------------------------------------------------------------------------
// Streaming. mpack_read and mpack_write keep state in a mpack_tokbuf_t so a
// token may arrive (or leave) split across calls. Each harness starts from ANY
// state the invariant allows and checks one call against the spec, so by
// induction over calls, any split of a byte stream gives the same tokens as
// reading it whole, and any split of the output gives the encoding.

// Reader invariant: either nothing pending (plen == 0), or the first ppos bytes
// of a header of plen bytes (ppos < plen, plen = header size of pending[0]).
// passthrough is any count of payload bytes still to pass as CHUNK tokens; a
// header is never pending while payload is (mpack_read sets one at a time).
// With nothing pending, ppos is 0 (mpack_read subtracts it from what it
// consumed). mpack_tokbuf_init sets this state, and h_read shows every call
// keeps it. A tokbuf used by mpack_write does not keep it (it leaves ppos set
// after a chunk), so one tokbuf must not serve both directions: Neovim and
// libmpack's rpc/object code use separate reader and writer tokbufs.
static void any_reader(mpack_tokbuf_t *tb) {
  tb->passthrough = nondet_u32();
  tb->plen = nondet_size(); tb->ppos = nondet_size();
  if (tb->passthrough) __CPROVER_assume(tb->plen == 0);
  if (tb->plen == 0) __CPROVER_assume(tb->ppos == 0);
  if (tb->plen) {
    __CPROVER_assume(tb->ppos >= 1 && tb->ppos < tb->plen);
    __CPROVER_assume(ref_layout((uint8_t)tb->pending[0]).kind >= 0);
    __CPROVER_assume(tb->plen == ref_hdr((uint8_t)tb->pending[0]));
  }
}

void h_tokbuf_init(void) {
  mpack_tokbuf_t tb;
  mpack_tokbuf_init(&tb);
  __CPROVER_assert(tb.plen == 0 && tb.ppos == 0 && tb.passthrough == 0, "starts empty");
}

void h_read(void) {
  mpack_tokbuf_t tb; any_reader(&tb);
  mpack_tokbuf_t old = tb;
  size_t n = nondet_size();
#ifndef MPACK_FIXED_CHUNK
  // Upstream passes an empty chunk (no progress) when n is a multiple of
  // 2^32 (findings/mpack-chunk-over-4gib.md); proved below 4 GiB only.
  __CPROVER_assume(n <= 0xffffffffu);
#endif
  const char *in = malloc(n);   // the whole input as one object (CHUNK tokens point into it)
  const char *b = in; size_t bl = n;
  mpack_token_t tok;
  int st = mpack_read(&tb, &b, &bl, &tok);
  __CPROVER_assert(bl == n - (size_t)(b - in) && b >= in, "buflen tracks buf");
  if (n == 0) {
    __CPROVER_assert(st == MPACK_EOF && b == in && tb.plen == old.plen && tb.ppos == old.ppos
                     && tb.passthrough == old.passthrough, "empty input: nothing changes");
    return;
  }
  if (old.passthrough) {
    uint32_t want = n < old.passthrough ? (uint32_t)n : old.passthrough;
    __CPROVER_assert(st == MPACK_OK && tok.type == MPACK_TOKEN_CHUNK && tok.data.chunk_ptr == in
                     && tok.length == want && b == in + want && tb.passthrough == old.passthrough - want,
                     "payload passes through as one chunk of min(input, remaining)");
    __CPROVER_assert(tb.plen == 0 && tb.ppos == 0, "invariant kept");
    return;
  }
  // The bytes of the pending header followed by the input.
  uint8_t y[9]; size_t have = old.plen ? old.ppos : 0;
  for (size_t i = 0; i < have; i++) y[i] = (uint8_t)old.pending[i];
  size_t take = n < 9 - have ? n : 9 - have;
  for (size_t i = 0; i < take; i++) y[have + i] = (uint8_t)in[i];
  ref_tok r; size_t used = 0; uint32_t need = 0;
  int rs = ref_decode(y, have + take, &r, &used, &need);
  if (rs == R_ERROR) {
    __CPROVER_assert(st == MPACK_ERROR && tb.plen == old.plen && tb.ppos == old.ppos && b == in, "invalid byte -> error, state kept");
    return;
  }
  if (rs == R_EOF) {
    __CPROVER_assert(st == MPACK_EOF && b == in + n, "short header: input consumed");
    __CPROVER_assert(tb.plen == need + 1 && tb.ppos == have + n && tb.passthrough == 0, "pending grows");
    size_t i = nondet_size(); __CPROVER_assume(i < tb.ppos);
    __CPROVER_assert((uint8_t)tb.pending[i] == y[i], "pending holds the header bytes");
    return;
  }
  __CPROVER_assert(st == MPACK_OK && same_token(&tok, &r), "token = spec token of the joined header");
  __CPROVER_assert(b == in + (used - have), "consumes the rest of the header only");
  __CPROVER_assert(tb.plen == 0 && tb.ppos == 0, "nothing pending");
  __CPROVER_assert(tb.passthrough == (r.type == T_STR || r.type == T_BIN || r.type == T_EXT ? r.length : 0),
                   "payload of str/bin/ext follows as chunks");
}

// A token as Neovim builds them for writing (mpack_pack_* in conv.c): any type
// but CHUNK; SINT holds a negative 64-bit value; ext type 0..127 (mpack_wext
// asserts it; lmpack's packer checks it); a float is 4 bytes (bits in lo) or 8.
// Returns 0 for a float of another length, which must be refused.
static int any_token(mpack_token_t *tok, ref_tok *k) {
  int ty = nondet_int();
  __CPROVER_assume(ty >= MPACK_TOKEN_NIL && ty <= MPACK_TOKEN_EXT && ty != MPACK_TOKEN_CHUNK);
  tok->type = (mpack_token_type_t)ty;
  tok->length = nondet_u32();
  *k = (ref_tok){ty, tok->length, 0, 0, 0};
  if (ty == MPACK_TOKEN_EXT) {
    tok->data.ext_type = nondet_int();
    __CPROVER_assume(tok->data.ext_type >= 0 && tok->data.ext_type < 0x80);
    k->ext_type = tok->data.ext_type;
  } else if (ty <= MPACK_TOKEN_FLOAT) {
    tok->data.value.lo = nondet_u32(); tok->data.value.hi = nondet_u32();
    k->lo = tok->data.value.lo; k->hi = tok->data.value.hi;
    if (ty == MPACK_TOKEN_SINT) __CPROVER_assume(k->hi >= 0x80000000u);
    if (ty == MPACK_TOKEN_FLOAT) {
      if (tok->length != 4 && tok->length != 8) return 0;
      if (tok->length == 4) __CPROVER_assume(k->hi == 0);
    }
  }
  return 1;
}

// A chunk token over a fresh object of exactly its length.
static void any_chunk(mpack_token_t *tok) {
  tok->type = MPACK_TOKEN_CHUNK;
  tok->length = nondet_u32();
  tok->data.chunk_ptr = malloc(tok->length);
}

// Writer invariant: nothing pending (plen == 0); or a header in progress:
// pending[0..plen) is the encoding of pending_tok and ppos < plen bytes of it
// are out; or a chunk in progress: plen == its length and ppos < plen bytes
// of it are out.
void h_write(void) {
  mpack_tokbuf_t tb;
  tb.plen = nondet_size(); tb.ppos = nondet_size(); tb.passthrough = nondet_u32();
  uint8_t enc[9]; int elen = 0; int pending_ok = 1;
  if (tb.plen) {
    if (nondet_int()) {
      any_chunk(&tb.pending_tok);
      __CPROVER_assume(tb.plen == tb.pending_tok.length && tb.ppos < tb.plen);
    } else {
      ref_tok pk;
      __CPROVER_assume(any_token(&tb.pending_tok, &pk));
      elen = ref_encode(&pk, enc);
      __CPROVER_assume(tb.plen == (size_t)elen && tb.ppos >= 1 && tb.ppos < tb.plen);
      for (int i = 0; i < elen; i++) tb.pending[i] = (char)enc[i];
    }
  }
  mpack_tokbuf_t old = tb;
  // The token passed in (ignored while something is pending).
  mpack_token_t t; ref_tok k; int valid = 1;
  if (nondet_int()) any_chunk(&t); else valid = any_token(&t, &k);
  size_t n = nondet_size();
  __CPROVER_assume(n >= 1);                    // mpack_write asserts *buflen
  char *out = malloc(n);
  char *o = out; size_t ol = n;
  int st = mpack_write(&tb, &o, &ol, &t);
  __CPROVER_assert(o >= out && ol == n - (size_t)(o - out), "buflen tracks buf");
  size_t w = (size_t)(o - out);

  const mpack_token_t *cur = old.plen ? &old.pending_tok : &t;
  if (cur->type == MPACK_TOKEN_CHUNK) {
    size_t done = old.plen ? old.ppos : 0, rest = cur->length - done;
    size_t cnt = rest < n ? rest : n;
    __CPROVER_assert(w == cnt, "writes min(rest of chunk, room)");
    size_t i = nondet_size(); __CPROVER_assume(i < cnt);
    __CPROVER_assert(out[i] == cur->data.chunk_ptr[done + i], "chunk bytes in order");
    if (cnt == rest) __CPROVER_assert(st == MPACK_OK && tb.plen == 0, "chunk done");
    else __CPROVER_assert(st == MPACK_EOF && tb.plen == cur->length && tb.ppos == done + cnt
                          && tb.pending_tok.data.chunk_ptr == cur->data.chunk_ptr
                          && tb.pending_tok.type == MPACK_TOKEN_CHUNK && tb.pending_tok.length == cur->length, "chunk continues");
    return;
  }
  if (old.plen) {
    size_t rest = old.plen - old.ppos, cnt = rest < n ? rest : n;
    __CPROVER_assert(w == cnt, "writes min(rest of header, room)");
    for (size_t i = 0; i < 9; i++) if (i < cnt) __CPROVER_assert((uint8_t)out[i] == enc[old.ppos + i], "header bytes in order");
    if (cnt == rest) __CPROVER_assert(st == MPACK_OK && tb.plen == 0, "header done");
    else { __CPROVER_assert(st == MPACK_EOF && tb.plen == old.plen && tb.ppos == old.ppos + cnt, "header continues");
      __CPROVER_assert(tb.pending_tok.type == old.pending_tok.type && tb.pending_tok.type != MPACK_TOKEN_CHUNK, "pending token kept");
      for (int i = 0; i < 9; i++) if (i < elen) __CPROVER_assert(tb.pending[i] == old.pending[i], "pending bytes kept"); }
    return;
  }
  if (!valid) { __CPROVER_assert(st == MPACK_ERROR && w == 0, "bad float length -> error, nothing written"); return; }
  elen = ref_encode(&k, enc);
  size_t cnt = (size_t)elen < n ? (size_t)elen : n;
  __CPROVER_assert(w == cnt, "writes min(encoding, room)");
  for (size_t i = 0; i < 9; i++) if (i < cnt) __CPROVER_assert((uint8_t)out[i] == enc[i], "shortest encoding, in order");
  if (cnt == (size_t)elen) __CPROVER_assert(st == MPACK_OK && tb.plen == 0, "token done");
  else {
    __CPROVER_assert(st == MPACK_EOF && tb.plen == (size_t)elen && tb.ppos == cnt, "token continues");
    for (int i = 0; i < 9; i++) if (i < elen) __CPROVER_assert((uint8_t)tb.pending[i] == enc[i], "rest kept in pending");
    __CPROVER_assert(tb.pending_tok.type == t.type && tb.pending_tok.length == t.length, "pending token recorded");
    if (t.type == MPACK_TOKEN_EXT) __CPROVER_assert(tb.pending_tok.data.ext_type == t.data.ext_type, "pending ext type");
    else if (t.type <= MPACK_TOKEN_FLOAT) __CPROVER_assert(tb.pending_tok.data.value.lo == t.data.value.lo && tb.pending_tok.data.value.hi == t.data.value.hi, "pending value");
  }
}
