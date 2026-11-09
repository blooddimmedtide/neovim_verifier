# trunc_string writes buf[-1] when buflen is 0

File: src/nvim/message.c, trunc_string (pinned fork commit bc10c48, extraction sha256 c06ab95c6bcce0ca9c8f65e6e3a7b7624fd26f438b8b3f841b44e61bc334e916).

When `buflen == 0` and `s` is a short non-empty string (for example `"ab"` with `room_in == 0`),
the "text fits without truncating" branch computes `len = (strlen(s) clamped to buflen - 1) - e + 1 = 0`
and then runs `buf[e - 1] = NUL` with `e == 0`, a one-byte write before the buffer.

- CBMC: `cbmc harness.c -DSN=3 -DBN=3 -DMINBUF=0 -DCHECKSPEC=0 --bounds-check --pointer-check --unwind 5 --unwinding-assertions`
  reports `buf[e - 1]` out of bounds (line 63 of the extraction).
- ASan: `gcc -fsanitize=address,undefined cbmc/repro_buflen0.c` reports heap-buffer-overflow WRITE of size 1.

Severity: low. The in-tree callers checked so far pass a positive buffer length
(msg_strtrunc passes `(room + 2) * 18` with `room > 0`). Not all callers were audited before the deadline.
Fix (not yet written or proved): return early when `buflen <= 0`.

Also suspected, not yet confirmed: with multibyte input, the inner copy loop can leave `e == buflen + 1`,
which would make the same branch write `buf[buflen]`. Needs a multibyte model to check.
