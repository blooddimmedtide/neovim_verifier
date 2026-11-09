# put_time returns FAIL on every successful write (src/nvim/fileio.c)

Pinned: verified_neovim 7b87ce82, `put_time`.

```c
return fwrite(buf, sizeof(uint8_t), ARRAY_SIZE(buf), fd) == 1 ? OK : FAIL;
```
`fwrite` returns the number of items written: 8 when everything is written. So the function
returns FAIL when the write succeeds, and OK only after a short write of exactly 1 byte. That is
the opposite of its doc ("@return FAIL when the write failed").

Impact: low today. The only caller (spellfile.c `write_vim_spell`, `<timestamp>`) ignores the
result, so no wrong behaviour is visible; any future caller that checks it would treat every
good write as an error. Not a memory-safety issue.

Found by: CBMC harness `fileio/cbmc_put/harness.c` (`h_put_time`, counterexample on any time
value with a full write). Reproducer: `put-time-return-repro.c` (glibc, ASan+UBSan):
`put_time on a good file returned FAIL, file size 8`.

Fix: blooddimmedtide/verified_neovim branch `fix-put-time-return` (compare with `== ARRAY_SIZE(buf)`).
The fixed function is proved against its documented contract for every time value and every
possible fwrite result, on both char signednesses.
