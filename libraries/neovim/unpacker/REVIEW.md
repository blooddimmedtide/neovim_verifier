# Independent adversarial review: msgpack_rpc/unpacker.c (CBMC)

Reviewer: fresh agent, no context from the author. Reviewed `CLAIM.md`, `cbmc/build.py`,
`cbmc/spec.h`, `cbmc/harness.c`, `cbmc/harness_ad.c`, `cbmc/run_cbmc.sh`, `cbmc/stubs/`, against
upstream `/home/user/nv-pin` (7b87ce8) and the fork `verified_neovim` 76c51e8.

## Verdict: **accept with changes**

The token-reader proofs (`unpack_string`, `unpack_array`, `unpack_integer`,
`unpack_uint_or_sint`) are sound and non-vacuous: the reference is written from the MessagePack
spec, the real mpack reader is included, buffers are exact-size, and every planted bug in them
was caught. The `push_additional_data` proof finds the real 4 GiB bug upstream and passes on the
fix, but the harness is weaker than the claim (issues 1-3); fix those before sign-off.

Reproduced: `run_cbmc.sh /home/user/nv-pin`: all proved except `h_push_additional_data`
(nbytes assertion fails, both signednesses; the expected finding). `MODE=fixed run_cbmc.sh
/home/user/verified_neovim`: all 14 runs proved.

## Issues

1. **The push_additional_data bound is 2^40, not 2^48 (CLAIM overstates).** `harness_ad.c` sets
   `MAXLEN` to `1 << 40` under `#ifndef`, and `run_cbmc.sh` never passes `-DMAXLEN`. The claim
   table ("every buffer length below 2^48") and the finding section ("proved for all sizes below
   2^48") are therefore wrong for the shipped script. I ran the fixed code with
   `-DMAXLEN=((size_t)1<<48)` and with `1<<55`: both VERIFICATION SUCCESSFUL, so the fix is fine.
   Change the default to `1 << 48` (or pass it from `run_cbmc.sh`).

2. **Vacuity: `size == 0` is never checked.** `__CPROVER_assume(k < size)` has no solution when
   `size == 0`, so every path that pushes an empty item is cut. Mutant m13
   (`a->nitems += (size != 0)`) survives. Callers never push 0 bytes (an item is at least a
   key and a value), but the claim says "for all sizes". Fix: assume
   `k < size || (size == 0 && k == 0)` and guard the byte assertion with `if (size)`.

3. **Old builder bytes are not checked (frame).** The harness checks the header, the size and the
   new bytes, but not that the bytes already in the builder stay as they were, which "appends"
   promises. Mutant m17 (zero the earlier payload before appending) survives. Fix: pick a
   nondet `j` in `[sizeof(AdditionalData), old)` when `old > sizeof(AdditionalData)`, save
   `ad.items[j]` before the call and assert it after. I checked this strengthened harness
   (both 2 and 3, bound 2^48): fixed code proved; upstream still fails on nbytes; m13 and m17
   both caught. Suggested text:

   ```c
   size_t k = nondet_size();
   __CPROVER_assume(k < size || (size == 0 && k == 0));
   char dk = size ? data[k] : 0;
   size_t j = nondet_size();
   int have_old = old > sizeof(AdditionalData);
   __CPROVER_assume(!have_old || (j < old && j >= sizeof(AdditionalData)));
   char oj = have_old ? ad.items[j] : 0;
   push_additional_data(&ad, data, size);
   ...
   if (size) assert(ad.items[base + k] == dk);
   if (have_old) assert(ad.items[j] == oj);
   ```

4. **`n0 < UINT32_MAX` is an undischarged precondition, and the fix leaves the same class of bug
   in `nitems`.** CLAIM says so honestly. Note: the fork made `nbytes` a `size_t` but `nitems`
   stays `uint32_t` and wraps on the 2^32-th push. Also `shada.c` adds `additional_data_len()`
   to the known field count in `uint32_t` (`arr_size = 2 + ... + nitems`, l.1393 and others), so
   near 2^32 items the written count wraps as well. Reaching that needs about 2^32 extra
   items (8 GiB or more) in one entry, which is no easier than the finding itself. Either bound
   it in shada.c (reject entries whose extra count would overflow) or say in the finding that
   the fix covers bytes only. This is outside the proved file, so it does not block.

5. **The uint64 >= 2^63 decision: "documented" is not supported.** The spec pins the code's
   two's complement reinterpretation, which is a decision taken from the code, not from the
   MessagePack spec (the spec only says uint64 is an unsigned 64-bit value; an int64 consumer
   should reject it or say how it maps it). That is fine if it is labelled as a decision, but:
   (a) `runtime/doc/api.txt` documents no such conversion; the only support is the same cast in
   `api_parse_enter` (unpacker.c l.96). Replace "the documented `Integer` conversion" with "the
   same cast used by `api_parse_enter`". (b) `(Integer)` of an out-of-range `uint64_t` is
   implementation-defined in C (C11 6.3.1.3p3); the proof holds for gcc/clang (modular), which
   CLAIM should say. (c) `spec.h` computes `*wrapped` but no harness uses it, and its comment says
   "(see CLAIM.md, finding)" though it is not a finding. Use `wrapped` (e.g. a
   `__CPROVER_cover` on it, so the wrapped case is shown reachable) or drop it.

6. **Failure consumption for unpack_array / unpack_integer is only "stays in the buffer".**
   This matches upstream's doc ("does not keep data untouched on failure") and all callers
   abandon the entry on failure, so it is acceptable. Mutant m21 (skip to end of buffer on
   failure) survives for that reason; I count it as outside the contract, not a weakness.
   Keep the claim wording as it is.

7. **Prelude checks are by single line, not by block.** `CHECKS` confirms that lines such as
   `  char *data;` and `  size_t size;` exist somewhere in `defs.h`, which many structs
   contain. I checked by hand that `String` (defs.h l.81-84), `Integer`, `AdditionalData`
   (types_defs.h, both trees) and `AdditionalDataBuilder` match the prelude, so nothing is
   wrong today. Check each struct as one contiguous block so a future field cannot slip in.

8. Minor, no change needed: `--object-bits 8` leaves 56 offset bits, enough for objects of
   2^48 and the few objects the harnesses make; 2^48 covers the whole x86_64 user address
   space (2^47). The `xrealloc` stub (realloc, no failure) matches Neovim's never-NULL
   contract, and `len > 0` holds at every call through `kv_concat_len`, so the real
   `size ? size : 1` rule does not matter. The real `kvec.h`, `mpack_core.c` and `conv.c` are
   included unmodified and pinned. `spec.h` matches spec.md (fixstr a0-bf, str8/16/32 d9-db,
   bin8/16/32 c4-c6, fixarray 90-9f, array16/32 dc-dd, positive fixint 00-7f, negative fixint
   e0-ff, uint8-64 cc-cf, int8-64 d0-d3, big-endian) and does not copy the code's structure.
   `parse_nop` / `api_parse_exit` are empty, so their "proofs" show only that the bodies are
   empty; the pinned sha256 is the real evidence.

## Mutants (`cbmc/mutants.toml`)

22 planted, all different from `mutants_result.tsv`: 20 non-equivalent and in the contract,
18 caught by the shipped proof. m13 and m17 survive (issues 2 and 3) and are caught by the
strengthened harness above. m19 is equivalent (`STRING_INIT` written out); m21 changes
behaviour the contract leaves open (issue 6). Score after issues 2-3 are fixed: 20/20.

| id | harness | bug | result |
|---|---|---|---|
| m01 | unpack_string | data not advanced past payload | caught |
| m02 | unpack_string | bin rejected | caught |
| m03 | unpack_string | EOF from reader ignored | caught |
| m04 | unpack_string | fit check off by one | caught |
| m05 | unpack_string | returns remaining size as length | caught |
| m06 | unpack_array | count truncated to int16 | caught |
| m07 | unpack_array | EOF ignored | caught |
| m08 | unpack_integer | EOF ignored | caught |
| m09 | unpack_uint_or_sint | uint truncated to 32 bits | caught |
| m10 | unpack_uint_or_sint | sint truncated to 32 bits | caught |
| m11 | unpack_uint_or_sint | res written on failure | caught |
| m12 | unpack_integer | float accepted | caught |
| m13 | push_additional_data | empty push not counted | **survived** (issue 2) |
| m14 | push_additional_data | header made only when capacity 0 | caught |
| m15 | push_additional_data | nbytes overwritten | caught |
| m16 | push_additional_data | header 4 bytes short | caught |
| m17 | push_additional_data | old payload zeroed | **survived** (issue 3) |
| m18 | push_additional_data | pushed byte corrupted | caught |
| m19 | unpack_string | equivalent | survived (equivalent) |
| m20 | unpack_array | failure returns -2 | caught |
| m21 | unpack_array | failure skips to end | survived (unspecified) |
| m22 | unpack_string | bin payload pointer off by one | caught |
