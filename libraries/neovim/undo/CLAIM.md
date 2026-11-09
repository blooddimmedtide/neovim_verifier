---
entry: neovim/src/nvim/undo.c (undo-file byte readers and writers) + get2c/get4c/get8ctime of src/nvim/fileio.c
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-s21m3m, commit 6cde603, PR #8 into verified)
toolchain: CBMC 6.4.1, Frama-C 33.0 WP with Z3 + CVC5 (tools/install.sh)
strength: candidate   # needs the independent review, planted bugs and owner sign-off
platform: x86_64, char signed and unsigned (both proved)
---

# Claim card: Neovim undo-file byte helpers

These functions turn undo-file bytes into numbers, strings and positions (`:rundo`, `'undofile'`)
and back. The undo file is untrusted input, so these are the first layer of its parser.

## What is proved

| Function | Property | Tool, inputs |
|---|---|---|
| `undo_write_bytes(bi, nr, len)`, 1 <= len <= 8 | on success writes exactly `len` bytes whose big-endian value is `nr mod 256^len`; returns false when the write fails (in the model a failed write writes nothing; a real partial write is not modeled) | CBMC, every `nr`, every len |
| `undo_write(bi, p, len)` | returns whether `fwrite` wrote the one item (inside every write harness) | CBMC |
| `put_header_ptr(bi, uhp)` | writes 4 bytes: `uhp->uh_seq`, or 0 for NULL | CBMC, every seq >= 0 |
| `serialize_pos`, `serialize_visualinfo` (writes that succeed) | lnum, col, coladd (then vi_mode, vi_curswant) as 4-byte big-endian fields holding the low 32 bits | CBMC, every value |
| `undo_read_4c` / `get4c` | the next 4 bytes, big-endian, read as a 32-bit two's complement int; -1 when fewer than 4 bytes are left; consumes 4 bytes (or all that is left) | CBMC, every 0..6 byte stream |
| `undo_read_2c` / `get2c` | the next 2 bytes big-endian (0..65535), or -1 | CBMC, every 0..3 byte stream |
| `undo_read_byte` | the next byte, or EOF | CBMC |
| `undo_read_time` / `get8ctime` (fixed fork) | the next 8 bytes big-endian as a 64-bit two's complement time_t, or -1; no undefined behavior | CBMC, every 0..9 byte stream |
| `undo_read_len` | the 4-byte field when it is >= 0 and, when the file size is known (> 0), no larger than the bytes left after it (an `ftell` failure counts as invalid); otherwise -1 with exactly one corruption report, naming the field, or "truncated" when the field itself was cut off | CBMC, every 0..6 byte stream, every file size, ftell success or failure |
| `unserialize_pos` | three 4-byte fields, each negative value (and -1 at EOF) replaced by 0 | CBMC, every 0..13 byte stream |
| `unserialize_visualinfo` | two such positions, then vi_mode and vi_curswant as read | CBMC, every 0..33 byte stream |
| `uhp_seq_cmp` | -1 / 0 / 1 as the first header's uh_seq is below / equal to / above the second's | CBMC, every pair |
| `uhp_table_find(t, n, seq)` | on a table sorted on uh_seq: an index i < n with `t[i]->uh_seq == seq` when one exists, else -1; reads nothing outside `t[0..n-1]` and the headers; terminates | Frama-C WP, any n (33/33 goals, plus 8/8 smoke tests: the preconditions are not contradictory); CBMC n <= 4 as a cross-check |
| `undo_read(bi, buf, size)` | for size > 0: true and buf = the next size bytes when that many are left, else false and buf all zeros; for size 0: false (C's fread returns 0), which no caller passes | CBMC, every stream length and size below 2^40 (callers pass at most a few hundred bytes or an int length); size <= 5 also checked index by index |
| `undo_read_string(bi, len)` | NULL (nothing leaked) when fewer than len bytes are left, else a len+1 block with those bytes and a NUL | CBMC, every stream length and len below 2^40 (callers pass a non-negative int) |

Every CBMC run also checks bounds, pointers, signed overflow, undefined shifts and memory leaks,
with every loop fully unwound (`--unwinding-assertions`). The fixed-field readers are checked on
streams up to a few bytes past the field, and they read a fixed number of bytes, so a longer
stream behaves like the longest one checked. `undo_read`/`undo_read_string` are checked for any
length below 2^40 with one nondeterministic index standing for every index (`h_read_any`,
`h_read_string_any`; a planted wrong expectation and a shortened memset both fail).

The reference (`cbmc/spec.h`) is written from the documented format ("MSB first", "-1 when
encountering EOF") with integer arithmetic on 128-bit values, not from the code's shifts.
Choices the reference takes from the code: -1 for EOF, which also equals the value of the bytes
FF FF FF FF (get4c cannot tell them apart; `undo_read_len` rejects both).

## Finding

`get8ctime` (fileio.c) overflows a signed shift when the timestamp's first byte is >= 0x80:
undefined behavior reachable from any undo or `.sug` file. See
`../findings/get8ctime-shift-overflow.md`. Upstream fails `h_read_time`; the fixed fork passes.
Upstream issue draft: project folder `neovim-verify/upstream/undo/` (not filed).

## What the proof relies on

- A model of stdio (`cbmc/model.h`): `getc` returns the next byte or EOF, `fread` of one item
  copies what is left and returns 1 only when all of it was there, `fwrite` writes everything or
  fails (nondeterministically) and writes nothing, `vim_ftell` returns the position or -1,
  `feof` is set by a read that hits the end; `fread`/`fwrite` of size 0 return 0 (C11 7.21.8).
  Read errors (EIO) are not modeled: a read either gets the byte or meets end of file.
  `corruption_error` only records the call and its message.
  `xmallocz` never returns NULL (Neovim exits on OOM) and NUL-terminates.
- `u_header_T` is reduced to its `uh_seq` field, the only one these functions read.
- gcc/clang's documented conversion of out-of-range unsigned values to signed types (modulo
  2^N), used by `get4c` and the fixed `get8ctime`.
- Preconditions: `undo_write_bytes` needs 1 <= len <= 8 (asserts len > 0; its buffer holds 8;
  callers pass 1, 2, 4, 8). `put_header_ptr` needs `uh_seq >= 0` (asserted).
  `uhp_table_find` needs `num_head >= 0` (the only caller checks `undo_read_len` >= 0 first) and
  a table sorted on uh_seq (the caller qsorts it with `uhp_seq_cmp` just before).
- The WP proof adds two `assert`s inside `uhp_table_find` (proved goals, not assumptions).

## Review

Independent adversarial review: `REVIEW.md` (accept with changes). Issues 1 (size-0 fread
model) and 3 (message not checked) are fixed in the model and harnesses; 2, 4 and 6 are reflected
in the wording above; 5 was already done. Planted bugs: 22 reviewer-chosen mutants
(`mutants.toml`, `run_mutants.py`), 22/22 caught (`mutants_result.tsv`).

## Not covered yet

All other undo.c functions (see PLAN.md). Sizes of 2^40 and more for `undo_read` /
`undo_read_string` (no caller can pass them).

## Evidence

```
bash cbmc/run_cbmc.sh <upstream tree>   # all proved except h_read_time (the finding)
bash cbmc/run_cbmc.sh <fixed tree>      # all proved
bash wp/run_wp.sh <tree>                # uhp_table_find 33/33
ONLY=h_table_find bash cbmc/run_cbmc.sh <tree>   # bounded cross-check (slow)
```
