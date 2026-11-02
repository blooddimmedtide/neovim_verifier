# Independent review: Neovim `src/mpack/mpack_core.c` (CBMC 6.4.1)

Reviewer: independent (did not write the proof). Date: 2026-11-02.
Subject: `CLAIM.md`, `cbmc/spec.h`, `cbmc/harness.c`, `cbmc/run_cbmc.sh`, `findings/mpack-chunk-over-4gib.md`,
fix `verified_neovim@1778674`. Upstream checked at 7b87ce822e6f.

## Verdict: **accept with changes**

The reference decoder/encoder is correct against the MessagePack spec, the harnesses are not vacuous, the
finding is real and the fix is correct and minimal. Two non-equivalent planted bugs survive, though. Both
come from post-states that are not fully asserted, so the "invariant holds again after every call"
induction in CLAIM.md is **not proved as stated** for `mpack_write`, and the ERROR contract of `mpack_read`
is weaker than claimed. Both gaps close with a few added assertions, and I checked that the stronger harness
still proves upstream (below). Re-run everything and record the result before admission.

## Reproduced

- `run_cbmc.sh` upstream: 10/10 proved (5 harnesses × signed/unsigned char), about 5 min. Fixed fork
  (`git show 1778674:src/mpack/mpack_core.c`): 10/10 proved.
- Upstream `h_read` without the `n <= 0xffffffff` assumption: FAILS (counterexample with n ≥ 2^32), so the
  finding comes from the proof as described.
- Reproducer: upstream prints `chunk length 0, 4294967296 bytes left` forever; the fixed file passes the
  whole 4 GiB−1 payload, then the last byte.

## Blocking findings

### B1. `h_write` does not re-establish its own pre-state invariant (pending token not checked)
`h_write` *assumes* the pending-header state is "`pending[0..plen)` is the encoding of `pending_tok`,
1 ≤ ppos < plen", but in the "token continues" branch it asserts only `plen`, `ppos` and the `pending` bytes.
It never asserts that `pending_tok` was recorded. The "header continues" and "chunk continues" branches
also don't assert that `pending_tok`'s type and length are kept. So the induction step is missing a conjunct.

Planted bug `wr-hdr-save-tok` (delete `tokbuf->pending_tok = tok;` in the small-buffer path of
`mpack_write`) **passes all 10 proofs**, yet it corrupts real output. After a CHUNK that needed two calls,
`pending_tok` still holds that chunk. The next header that does not fit is then continued as a chunk.
`scratchpad/rev-mpack/demo/demo.c`: upstream writes `… da 01 2c`; the mutant writes `… da 42 43 44 …`
(payload bytes in place of the str 16 length). `difftest` would likely catch it, but the CBMC claim does not.

**Fix:** after the call, assert the full writer invariant. In practice: on "token continues",
`pending_tok.type == t.type && length == t.length` and its value/ext_type are equal. On "header continues",
`pending_tok.type` is unchanged and not CHUNK, and the `pending` bytes are unchanged. On "chunk continues",
`pending_tok.type == CHUNK && pending_tok.length == cur->length`. Better: write one `writer_inv(tb)`
predicate and use it both to build the pre-state and to check the post-state.

### B2. `mpack_read` ERROR: buffer position not checked
CLAIM.md says that on `MPACK_ERROR` mpack_read returns "without changing the state". The harness asserts only
`st`, `plen` and `ppos`. Planted bug `rd-error-moves-buf` (consume the 0xc1 byte before returning ERROR)
**passes all 10 proofs**. `mpack_parse` restores `buf` on ERROR, but `mpack_rpc_receive` (rpc.c) and
`unpacker_parse_header` do not.
**Fix:** add `b == in` (and `tb.passthrough == old.passthrough`) to the ERROR assertion.

I applied both fixes in a copy (`scratchpad/rev-mpack/harness_strong.c`). It kills both mutants
(`pending token recorded`, `invalid byte -> error, state kept` fail), and upstream still proves `h_read` and
`h_write`. I ran that check with signed char only; the owner should run both char modes.

## Non-blocking findings

1. **Spec provenance.** `spec.h` says the libmpack choices (sign bit clear → UINT, raw unsigned bits,
   width-sized `length` for SINT, ext type 0..255, EOF `tok->length` = header−1) are "documented
   (mpack_core.h)". They are not: `mpack_core.h` documents none of them. They are restated from the code
   (only the `mpack_wnint` comment in the .c hints at "not sign-extended"). The rest of `spec.h` (every first
   byte 0x00–0xff, header sizes, field widths, big-endian, ext/fixext layout with the type byte after the
   length, 0xc1 never used, shortest-encoding rules incl. negative fixint −32..−1, fixext preferred for
   1/2/4/8/16, no fix form for bin) matches the MessagePack spec. Reword as "observed libmpack behaviour,
   to be confirmed in the owner's sign-off", and list them in CLAIM.md as API choices, not spec facts.
2. **Stream claim wording.** "Reading a byte stream split at any points yields the same tokens as reading it
   whole" is false for CHUNK tokens: payload chunking follows the buffer splits. Say "the same non-CHUNK
   tokens, and CHUNK tokens whose concatenation is the same payload". The writer claim also depends on a
   caller protocol: after `MPACK_EOF`, call again without advancing (`*t` is ignored while `plen != 0`). All
   Neovim callers (object.c `mpack_unparse`, rpc.c) follow it by testing `tb->plen`. State this in CLAIM.md.
3. **Finding reachability is understated.** Besides PUC-Lua `vim.mpack.decode`, the hang is reachable in a
   *default (LuaJIT) build* through ShaDa. `shada_read_next_item` reads the first item of a ShaDa file whole
   when its type is unknown or `\n` (`verify_but_ignore`), regardless of the `s` size limit, then calls
   `unpack_skip` → `mpack_parse` on it (shada.c ~3170–3210). A crafted ShaDa file with a first item of
   4 GiB + 5 bytes (bin 32 header + 4 GiB) hangs startup, given 4 GiB of RAM. Severity stays low, but the
   "needs a PUC Lua build" sentence is wrong. I found this by reading the code and did not run it (4 GiB file).
   Other `mpack_parse` callers: `nvim__unpack` (RPC strings < 4 GiB; from Lua with LuaJIT < 2 GiB),
   `msgpackparse()` (blob length is `int`; list input goes through `ARENA_BLOCK_SIZE` chunks). Not reachable.
4. **Fix is correct and minimal:** `(mpack_uint32_t)MIN(*buflen, (size_t)passthrough)` ≤ passthrough fits
   in 32 bits. Note that `run_cbmc.sh` switches off the <4 GiB assumption by grepping for the exact fixed
   text, so a semantically identical rewrite of the fix would silently get the weaker precondition. Prefer
   an explicit flag.
5. **`h_rtoken` on EOF/ERROR** does not constrain `*buf`/`*buflen` (rtoken advances past the first byte on
   EOF). Neovim's direct `mpack_rtoken` callers in unpacker.c work on local copies or document "does not keep
   data untouched on failure", so this is fine. The claim card should say the position after EOF is unspecified.
6. **Huge objects.** `h_read` mallocs objects of up to SIZE_MAX bytes (n ≥ 2^60 is reachable, probe below).
   CBMC's offset field is narrower than 64 bits, but every accessed offset here is < 2^32 + 9, so I see no
   unsoundness. It is still worth a sentence in CLAIM.md.
7. **Preconditions** are justified by the callers I checked. SINT negative: `mpack_pack_sint`, and
   `mpack_pack_number`, whose non-negative-SINT results are filtered by the round-trip check. Ext type 0..127:
   checked by lmpack's packer, and `mpack_wext` asserts it. Float 4 with hi = 0: `mpack_pack_float_fast`; the
   writer ignores hi for 4-byte floats anyway, so this only serves the harness's round-trip check. Separate
   read/write tokbufs: rpc.c, object.c parsers and unpacker.c use separate ones. Nothing in Neovim touches
   tokbuf fields except reading `plen`.
8. The "one nondet index" checks (chunk bytes, pending bytes) are sound: the index is universally
   quantified, so any wrong byte is a counterexample. The `any_input` 9-byte-object trick is sound because
   `--pointer-check` would flag any read past the header.

## Vacuity (reachability probes, `scratchpad/rev-mpack/vac_harness.c`)
Every probe was reached, on fixed and upstream: rtoken OK on long input / sint64 / int16-as-UINT / ext32 /
float64, EOF needing 8 more bytes, fixext EOF, 0xc1. read: n = 0, partial and whole chunks, chunk with
n ≥ 4 GiB, n = 4 GiB and n ≥ 2^60 (fixed only; upstream excluded by its precondition as intended), ERROR, EOF
from empty and from pending (growing), OK completing from pending (uint64, have = 8, ext32), passthrough set,
long input. write: chunk new / continuing / finishing, `*t` ignored while a header or chunk is pending, header
continue/finish, bad float (also with n < 9), direct (n ≥ 9) and via pending, 9-byte token, negative fixint,
ext32. The only unreachable probe, "ERROR with a pending header", is excluded by the reader invariant (the
pending first byte is valid), which is correct. `mpack_tokbuf_init` establishes both invariants.

## Planted bugs
49 mutants of `mpack_core.c`, in `cbmc/mutants.toml` (with results). Each was run with
`run_cbmc.sh <nvim> <mutant>`: first with `ONLY` set to the harnesses that see the function, then, if it
survived, all 5 harnesses × 2 char modes.

**Score: 43 / 45 non-equivalent mutants caught. 4 survivors are equivalent; 2 survivors are spec gaps (B1, B2).**
`rt-advance-signed` is caught only by the signed-char run, which shows both char modes are needed.

Equivalence arguments:
- `rb-dead-init`: `mpack_rvalue` calls `mpack_value(type, remaining, mpack_byte(0), tok)` before reading,
  so the earlier `l.data.value.lo = 0` is dead.
- `rd-eof-ppos-reset`: under the reader invariant, `plen == 0 ⇒ ppos == 0`, so resetting `ppos` is a no-op.
  This equivalence relies on the invariant; for a tokbuf shared with the writer it would not hold, and
  CLAIM.md already excludes sharing.
- `rp-consume`: in that branch `ppos + count < plen` forces `count == *buflen`.
- `wn-hi-test`: `(hi && hi != ~0)` and `hi != ~0` differ only for `hi == 0`, i.e. a non-negative SINT, which
  the precondition excludes. A read token re-written would differ, which is already noted in the finding.

| id | function | planted bug | expect | result |
|---|---|---|---|---|
| `rt-fixmap-bound` | mpack_rtoken | 0x8f (fixmap 15) decoded as fixarray | caught | caught |
| `rt-fixstr-mask` | mpack_rtoken | fixstr length mask loses bit 4 (lengths 16..31) | caught | caught |
| `rt-negfixint-bound` | mpack_rtoken | map 32 (0xdf) decoded as a negative fixint | caught | caught |
| `rt-float-width` | mpack_rtoken | float 32/64 header sizes halved (2 and 4 bytes) | caught | caught |
| `rt-array-width` | mpack_rtoken | array 16/32 length fields read as 1/2 bytes | caught | caught |
| `rt-fixext-eof-len` | mpack_rtoken | incomplete fixext reports a 3-byte header; pending buffer sized wrongly | caught | caught |
| `rt-nil-length` | mpack_rtoken | nil token reports length 1 | caught | caught |
| `rt-true-value` | mpack_rtoken | true carries the raw byte instead of 1 | caught | caught |
| `rt-advance-signed` | ADVANCE (macro, all readers) | bytes >= 0x80 sign-extended where char is signed (only the signed-char run can see it) | caught | caught |
| `rv-eof-boundary` | mpack_rvalue | a value whose last byte ends the input is reported incomplete | caught | caught |
| `rv-hi-split` | mpack_rvalue | 64-bit value split into hi/lo at the wrong byte | caught | caught |
| `rv-shift` | mpack_rvalue | wrong byte placement (nibble shift) | caught | caught |
| `rv-sign16` | mpack_rvalue | int 16 sign test looks at bit 7 | caught | caught |
| `rv-sign64` | mpack_rvalue | int 64 sign test looks at the low word | caught | caught |
| `rb-ext-required` | mpack_rblob | ext 8/16/32 reads its type byte without checking it is there (out of bounds) | caught | caught |
| `rb-dead-init` | mpack_rblob | dead store: mpack_rvalue resets the value via mpack_value before reading | equivalent | survived: equivalent |
| `rd-empty-input` | mpack_read | empty input no longer returns early (empty chunk / state change) | caught | caught |
| `rd-chunk-cast16` | mpack_read | the 4 GiB truncation bug, moved to 64 KiB (inside the upstream precondition) | caught | caught |
| `rd-chunk-ptr` | mpack_read | chunk points one byte past the payload | caught | caught |
| `rd-passthrough-keep` | mpack_read | payload count never decreases | caught | caught |
| `rd-advanced` | mpack_read | header completed from pending consumes the already-pending bytes again | caught | caught |
| `rd-passthrough-map` | mpack_read | map count treated as payload bytes | caught | caught |
| `rd-pending-plen` | mpack_read | pending header one byte too long | caught | caught |
| `rd-error-as-eof` | mpack_read | 0xc1 reported as EOF | caught | caught |
| `rd-error-moves-buf` | mpack_read | ERROR consumes the bad byte (claim says ERROR changes nothing) | caught | survived: **spec gap (blocking)** |
| `rd-eof-ppos-reset` | mpack_read | reader invariant already has ppos == 0 whenever plen == 0 | equivalent | survived: equivalent |
| `rp-done-test` | mpack_rpending | header reported complete one byte early | caught | caught |
| `rp-consume` | mpack_rpending | in this branch count == *buflen (ppos + count < plen forces count = *buflen) | equivalent | survived: equivalent |
| `wp-fixint-bound` | mpack_wpint | 128 written as one byte 0x80 (a fixmap) | caught | caught |
| `wp-not-shortest` | mpack_wpint | 65535 written as uint 32: decodes right, but not the shortest encoding | caught | caught |
| `wn-int8-bound` | mpack_wnint | -128 written as int 16 (not shortest) | caught | caught |
| `wn-hi-test` | mpack_wnint | differs only for hi == 0, i.e. a non-negative SINT, which the precondition excludes | equivalent | survived: equivalent |
| `wn-fixint-byte` | mpack_wnint | negative fixint loses bit 4 of its value | caught | caught |
| `wf-swap64` | mpack_wfloat | float 64 words swapped | caught | caught |
| `ws-fixstr-bound` | mpack_wstr | 32-byte string header becomes 0xc0 (nil) | caught | caught |
| `wb-bin32-byte` | mpack_wbin | bin 32 header byte says bin 16 | caught | caught |
| `we-fixext8` | mpack_wext | fixext 8 written as fixext 16 | caught | caught |
| `we-ext8-order` | mpack_wext | ext 8 type and length bytes swapped | caught | caught |
| `wa-fixarray-bound` | mpack_warray | array of 16 written as 0x90 (empty array) | caught | caught |
| `wm-map32-byte` | mpack_wmap | map 32 written as array 32 | caught | caught |
| `w2-byte-order` | mpack_w2 | 16-bit fields little-endian | caught | caught |
| `w4-buflen` | mpack_w4 | buffer length not kept in step with the pointer | caught | caught |
| `wr-ignore-pending` | mpack_write | the token passed in is used even while one is pending | caught | caught |
| `wr-chunk-ppos` | mpack_write | a new chunk starts at a stale ppos | caught | caught |
| `wr-chunk-save-tok` | mpack_write | an unfinished chunk is not remembered | caught | caught |
| `wr-hdr-save-tok` | mpack_write | an unfinished header does not record its token; the next call dispatches on a stale pending_tok (e.g. an earlier CHUNK) and writes chunk bytes instead of the header | caught | survived: **spec gap (blocking)** |
| `wr-small-threshold` | mpack_write | a 9-byte token written straight into a 5..8 byte buffer (overflow) | caught | caught |
| `wr-hdr-ppos` | mpack_write | an unfinished header restarts from its first byte | caught | caught |
| `wpend-keep-plen` | mpack_wpending | a finished pending header stays pending | caught | caught |
## Required before admission
1. Add the B1 and B2 assertions (or a shared `writer_inv`), re-run `run_cbmc.sh` on upstream and fixed in
   both char modes, and confirm that `wr-hdr-save-tok` and `rd-error-moves-buf` are caught.
2. Update CLAIM.md: stream wording (CHUNK splits, caller protocol for EOF), spec provenance of the libmpack
   choices, ShaDa reachability in the finding.
