# Review: shada.c reading primitives

Adversarial self-check that the CBMC proofs in this directory are not vacuous, per
the project standard (at least 10 planted bugs, every non-equivalent one caught).

`mutants.toml` holds 12 planted bugs, one-line changes to the verbatim extraction,
spread across all five proved functions and every decoding branch:

- `msgpack_read_uint64`: wrong payload length for uint16/uint32/uint64, wrong
  positive-fixint mask, payload written at the wrong buffer offset, and EOF mapped
  to the wrong status — 6 bugs.
- `vim_be64toh`: byte shift off by one, and reading the wrong byte index — 2 bugs.
- `fread_len`: short read accepted as success, and the read-error branch disabled — 2.
- `sd_reader_skip`: short skip accepted as success — 1.
- `shada_check_status`: trailing bytes ignored (Success with `remaining != 0`) — 1.

`run_mutants.sh` applies each, runs `run_cbmc.sh`, and requires the proof to flip to
FAILED. Result: **12 / 12 caught** (signed and unsigned char, since `run_cbmc.sh`
proves both). So each property genuinely constrains the function; the proofs are not
passing by vacuity.

Scope note: this reviews only the five proved primitives. `shada_read_next_item` and
the rest of `shada.c` are not yet verified (see ../CLAIM.md and ../NOTES.md).
