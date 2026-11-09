# get8ctime: signed shift overflow on a timestamp whose first byte is >= 0x80

- File: `src/nvim/fileio.c`, `get8ctime()` (upstream 7b87ce8). Called by `undo_read_time()` in
  `src/nvim/undo.c` (undo header `uh_time`, file `seq_time`) and by `src/nvim/spellfile.c`
  (`.sug` timestamp, `SN_SUGFILE` section).
- Found by: CBMC harness `h_read_time` (`undo/cbmc/`, `--signed-overflow-check`):
  `get8ctime.overflow.1: arithmetic overflow on signed shl in n << 8`.
- Cause: the 8 bytes are accumulated in a signed `time_t`; after 7 bytes `n` holds up to 2^56 - 1,
  and `n << 8` cannot be represented when the first byte is >= 0x80. That is undefined behavior
  in C (C11 6.5.7p4).
- Reach: any undo file Neovim reads (`:rundo`, or `'undofile'` on buffer load) or `.sug` file. The
  content is attacker-controlled when a project ships its own undo/spell files or a shared
  `'undodir'` is writable by others.
- Impact: with today's gcc/clang at -O2 the shift wraps and the value is just a strange
  timestamp, so there is no known memory-safety effect. It is still undefined behavior that a
  compiler may exploit, and UBSan builds abort:
  `repro.c:15:12: runtime error: left shift of 36028797018963968 by 8 places cannot be represented in type 'long int'`.
- Reproducer: `findings/get8ctime-repro/repro.c` (verbatim function, 8 bytes `80 00 .. 01`).
- Fix: accumulate in `uint64_t`, return `(time_t)n` (the same implementation-defined
  unsigned-to-signed conversion `get4c` already uses). blooddimmedtide/verified_neovim PR #8,
  branch `claude/project-thread-s21m3m`, commit 6cde603. Proved: `h_read_time` passes on the
  fixed tree for every 0..9-byte stream, both char signednesses.
