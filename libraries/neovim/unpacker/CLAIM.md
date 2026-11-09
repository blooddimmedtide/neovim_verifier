---
entry: neovim/src/nvim/msgpack_rpc/unpacker.c (msgpack token readers)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-3l219g, commit 76c51e8)
toolchain: CBMC 6.11.0 (vpipe Nix toolchain)
strength: candidate   # becomes full-correctness after the owner signs off the spec
tools: CBMC (bit-precise; loop-free code plus the real mpack reader, unwinding assertions on)
platform: x86_64, char signed and unsigned (both proved)
status: IN PROGRESS: 7 of 16 functions have proofs; 9 open (listed below). The file is not done.
---

# Claim card: Neovim msgpack_rpc/unpacker.c

## What is proved, for every byte content and every buffer length below 2^48

Nothing is stubbed on the reading side: `src/mpack/mpack_core.c` and `src/mpack/conv.c` are
included whole (sha256 pinned in `cbmc/pins.txt`), so the proofs cover the real `mpack_rtoken`,
`mpack_unpack_uint` and `mpack_unpack_sint`. The buffer is an exact-size object, so any read
past its end fails `--pointer-check`. References in `cbmc/spec.h` are written from the
MessagePack specification, not the code.

| Function | Property | Evidence |
|---|---|---|
| `unpack_string(&d, &s)` | If the buffer starts with a str/bin header (fixstr, str8/16/32, bin8/16/32) whose payload fits, returns (pointer to payload, payload length), non-NULL even for length 0, and advances d/s past header and payload. Otherwise returns {NULL, 0} and leaves d and s unchanged | `h_unpack_string` |
| `unpack_array(&d, &s)` | If the buffer starts with an array header (fixarray, array16/32), returns its item count and consumes exactly the header. Otherwise -1; consumption stays inside the buffer (d + s unchanged) | `h_unpack_array` |
| `unpack_integer(&d, &s, &res)` | If the buffer starts with a complete integer (pos/neg fixint, uint8..64, int8..64), returns true, sets res to its value and consumes exactly it. Otherwise false, res untouched, consumption stays inside the buffer | `h_unpack_integer` |
| `unpack_uint_or_sint(tok, &res)` | For every token the real reader produces: true and the integer value for UINT/SINT tokens, false and res untouched otherwise | `h_unpack_uint_or_sint` |
| `parse_nop`, `api_parse_exit` | empty; read and write nothing | `h_parse_nop`, `h_api_parse_exit` |
| `push_additional_data(ad, data, size)` (fixed fork) | appends the bytes after an AdditionalData header (created zeroed on first use), nitems + 1, and keeps `nbytes == total size - header`. Upstream: wrong from 4 GiB (finding) | `harness_ad.c` |

Reference decision (stated, not derived): a msgpack uint64 of 2^63 or more has no `Integer`
value. The code returns its two's complement reinterpretation (value - 2^64) and the proof
pins exactly that; callers see e.g. 18446744073709551615 as -1. Recorded as a note, not
fixed: it is the documented `Integer` conversion used throughout the API.

Harness preconditions (listed per AGENT_PROMPT): buffer lengths below 2^48 (more than the
x86_64 address space); `xrealloc` never returns NULL (Neovim exits instead); for
`push_additional_data`, the builder already satisfies its own invariant and holds fewer than
2^32 - 1 items (one builder collects one msgpack map or array, whose count is a uint32; ShaDa
array entries can push both extra array elements and map keys into one builder, so this bound
is not documented upstream: say so if reviewing).

## Finding

`push_additional_data` adds `(uint32_t)size` to a `uint32_t nbytes`. Once the unknown keys
kept from one ShaDa entry reach 4 GiB, nbytes wraps and `dump_additional_data`
(`shada.c`) writes back only `nbytes mod 2^32` bytes while the map/array count still includes
every item: the rewritten ShaDa entry is malformed. CBMC counterexample: empty builder,
size = 2^39. Reachable only with a ShaDa item of 4 GiB or more read with the `s` limit of
'shada' disabled or raised. Fix (verified_neovim 76c51e8): `nbytes` becomes `size_t` and the
cast is dropped; proved for all sizes below 2^48. See `../findings/additional-data-over-4gib.md`.

## Not covered yet (file not done)

`unpack`, `api_parse_enter`, `unpacker_init`, `unpacker_teardown`,
`unpacker_parse_header`, `unpacker_advance`, `unpacker_parse_redraw`, `unpack_skip`,
`unpack_keydict`. These call `mpack_parse` (object.c), the arena allocator, the UI client
and the ShaDa key hash tables, and loop over unbounded input; they need Frama-C WP with
contracts for those callees. `unpack_keydict` also shifts `1ULL << field->opt_index`, which
is defined only while generated key sets have at most 64 fields (to check).

## Mutants

7 planted bugs, 7 caught (`cbmc/mutants_result.tsv`). No independent review yet.

## Reproduce

    bash libraries/neovim/unpacker/cbmc/run_cbmc.sh <neovim checkout at the pinned commit>
    MODE=fixed bash libraries/neovim/unpacker/cbmc/run_cbmc.sh <verified_neovim checkout at 76c51e8>
