---
entry: neovim/src/nvim/input.c (typeahead and stuff buffer functions; the file was getchar.c)
upstream: https://github.com/neovim/neovim
commit: 7b87ce822e6fd45a4d9993599c2854afdb0dc4dd
fixed_fork: https://github.com/blooddimmedtide/verified_neovim (branch claude/project-thread-2h2bgy, commit 4c11bf5, draft PR #12)
toolchain: Frama-C 33.0 WP, Z3, CVC5 (Nix, tools/install.sh); gcc + UBSan for the counter check
strength: candidate for the functions marked proved in PLAN.md; the rest are open
tools: Frama-C WP, -wp-rte -wp-model Typed+Cast -wp-smoke-tests, one run per function
platform: x86_64
---

# Claim card: input.c typeahead (typebuf) and stuff buffers (readbuf1/readbuf2)

Status per function, with goal counts: `PLAN.md`. Not finished: functions listed there as
open are not verified, and this file is not done until every one is.

## What is proved (for the functions marked proved)

Each contract is written from the comments in input.c and input_defs.h, not from the code:
the typebuf layout comment ("tb_buf[tb_off .. tb_off + tb_len - 1] are the chars ... must be
NUL", tb_noremap same length, counts are prefixes) is the predicate `tb_ok`; the StuffBuf
comment ("[read, keys.size) is unread", insert between read and size) is `sb_ok`.

- `free_buff`: frees the items, buffer becomes all zero, one allocation fewer.
- `read_readbuf`: NUL on an empty buffer; else the byte at `read`; with advance, moves `read`,
  resets all three positions when drained, keeps `insert >= read`. `sb_ok` is kept.
- `read_readbuffers`: byte from readbuf1 if it has a non-NUL byte, else from readbuf2.
- `start_stuff`, `stuff_empty`, `readbuf1_empty`, `typebuf_changed`, `typebuf_typed`,
  `typebuf_maplen`: exact result / effect.
- `init_typebuf`: sets up the static buffers once (offset MAXMAPLEN + 4, change count 1).
- `alloc_typebuf`: two new blocks of TYPELEN_INIT bytes, empty typebuf, counts reset, change
  count advanced (never 0), two allocations more.
- `free_typebuf`: frees the heap buffers, never the static ones.
- every function: no undefined behavior (-wp-rte: overflow, out-of-bounds, invalid pointers).

## What the proof relies on

1. Frama-C WP 33 + Z3 + CVC5 are sound for this code (Typed+Cast model). `-wp-smoke-tests`
   checks that no precondition or stub makes code dead (it caught a contradictory allocator
   stub during this work; the stubs were rewritten).
2. Extraction (`wp/build.py`): each function is the exact upstream text (sha256 pinned);
   ACSL is inserted as comments only and stripping them gives the source back. The prelude
   copies the types, enums and macros the functions use; every copied line is checked
   against the pinned headers. `assert(e)` is mapped to an ACSL assert (proved).
3. Stubs (`wp/stubs/vp_typebuf.h`, `vp_string.h`): memmove/memcpy/strlen per C11; xmalloc
   returns a valid block different from the blocks the caller names (ghost "avoid" arguments,
   because WP does not implement `\fresh`); xrealloc keeps the bytes in range; xfree; emsg
   may change typebuf (it flushes typeahead); state_no_longer_safe, internal_error, setcursor
   change nothing proved here.
4. Preconditions: the `tb_ok` / `sb_ok` invariants on entry; ins_typebuf/del_typebuf get an
   offset and length inside the typeahead; add_buff's `s` does not point into the buffer
   (documented) and sizes stay below SIZE_MAX / 4 (kv_roundup32 wraps to 0 near SIZE_MAX).
   Upstream only: `tb_change_cnt != INT_MAX` and, for ins_typebuf, string length at most
   INT_MAX - 5 * (MAXMAPLEN + 4). Both are the findings below.

## Findings

1. `ins_typebuf` truncates `strlen()` to int: `feedkeys()` with a 2^31-byte string segfaults
   (reproduced in Nvim 0.9.5). `../findings/ins-typebuf-strlen-truncation.md`.
2. `++typebuf.tb_change_cnt` overflows at INT_MAX (UB) before the wrap test. Confirmed with
   UBSan on the extracted code (`difftest/run_ubsan.sh`). `../findings/typebuf-change-cnt-overflow.md`.

Both fixed in verified_neovim 4c11bf5. Upstream issue drafts (not filed): `upstream-drafts/`.

## Observation (not a memory-safety bug)

ins_typebuf's second branch (empty typeahead, string longer than tb_off) does not write the
NUL that the layout comment says must follow the chars. The proved contract states the NUL
only where the code keeps it. No reader that depends on it was found.

## Not done

Planted-bug (mutant) review, independent review, differential test, CI run, Neovim test
suite on the fixed branch. See PLAN.md for the open functions.
