# encode.c / decode.c — Frama-C WP results

Upstream Neovim 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd. Function text is extracted verbatim and
sha256-pinned (`pins.txt`); `build.py` checks that stripping the `/*@ */` annotations gives the
pinned text back. Run: `bash run_wp.sh <neovim checkout at 7b87ce8> [timeout]`.

Settings: `-wp-rte -wp-smoke-tests -warn-signed-downcast -warn-signed-overflow -wp-model Typed+Cast`,
provers z3 + cvc5, no admits/axioms (the script rejects them). Run 2026-11-09 08:37 UTC.

| Function | File | Goals | Status |
|---|---|---|---|
| encode_blob_write | encode.c | 18/18 (smoke tests pass) | proved against trusted ga_concat_len contract |
| typval_parser_error_free | decode.c | 41/41 (smoke tests pass) | proved |

Spot mutants (contract changed, proof must fail): `ensures \result == len + 1` → 17/18;
treating MPACK_TOKEN_ARRAY as owning a buffer → 40/41. Both caught.

## What is assumed

- `ga_concat_len`: trusted contract (appends len bytes, keeps old bytes). It matches what the
  garray proof in PR #4 states; that proof was redone with ghost "avoid" allocator stubs and
  smoke tests (commit d51350b). No allocator stub is used here, so the contradictory garray
  `xrealloc` stub is not involved. `xfree` only decrements a ghost live count.
- `encode_blob_write` requires `len <= INT_MAX`: it returns `(int)len`, a signed downcast.
  Callers are msgpack packer writes with small chunks; this is a precondition, not a proof
  about callers.
- `typval_parser_error_free` requires `parser->size <= MPACK_MAX_OBJECT_DEPTH + 1` (the length of
  `items`). Not proved for callers (mpack_parse_tok keeps size below capacity).
- WP warns that union access (`data[1].p`) under the Typed model might be unsound; only the `p`
  member is read or written here.

## Still unverified (23 of 25 functions)

encode.c: encode_list_write, encode_read_from_list, encode_vim_list_to_buf, encode_init_lrstate,
encode_check_json_key, encode_tv2string, encode_tv2echo, encode_tv2json, conv_error,
convert_to_json_string (owned by another thread), plus the typval_encode.c.h template instances
(claimed by PR #6).

decode.c: create_special_dict, decode_create_map_special_dict, decode_string, parse_json_number,
parse_json_string, json_decoder_pop, json_decode_string, positive_integer_to_special_typval,
typval_parse_enter, typval_parse_exit, mpack_parse_typval, unpack_typval.

The library is not finished.
