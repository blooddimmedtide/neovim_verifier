# typebuf.tb_change_cnt: signed overflow in the wrap-around

**File:** src/nvim/input.c, `ins_typebuf()`, `del_typebuf()`, `alloc_typebuf()` and
`flush_buffers()`, upstream 7b87ce822e6f. **Found by:** Frama-C WP -wp-rte.

```c
if (++typebuf.tb_change_cnt == 0) {
  typebuf.tb_change_cnt = 1;
}
```

The test for 0 means the author expected wrap-around, but `++` on `INT_MAX` is signed
overflow, undefined behavior in C. With the usual wrapping it goes to INT_MIN and later
back through 0, so in practice the visible effect is small; with an optimizer that uses the
UB it may drop the `== 0` test. It needs about 2^31 typeahead changes (each typed or fed key
is one or more), so it is reachable in a long session or with a large `feedkeys()` loop, but
we did not reproduce it in a running Nvim. UBSan on the extracted upstream `del_typebuf` (`typebuf/difftest/run_ubsan.sh`) reports "signed integer overflow: 2147483647 + 1"; the fixed code passes (counter becomes 1).

The upstream proof requires `typebuf.tb_change_cnt != INT_MAX`.

## Fix

verified_neovim 4c11bf5: `if (typebuf.tb_change_cnt == INT_MAX || ++typebuf.tb_change_cnt == 0)`,
so the counter goes from INT_MAX to 1 and stays non-zero. Proved (fixed mode) for
ins_typebuf, del_typebuf, alloc_typebuf.
