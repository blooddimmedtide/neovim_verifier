# ops.c get_vts_sum: signed int overflow on a large 'vartabstop' shift

**Where:** `src/nvim/ops.c` `get_vts_sum` (pinned upstream 7b87ce8), called from
`get_new_vts_indent` / `shift_line`.

**What:** with `'shiftwidth'` = 0 and `'vartabstop'` set, a shift uses `get_new_vts_indent`,
which calls `get_vts_sum(vts_array, vtsi + amount)`. `amount` is the Visual-mode count
(`op_shift(oap, true, oap->is_VIsual ? cap->count1 : 1)`, count capped at 999999999), and
`get_vts_sum` computes `vts_array[vts_array[0]] * (index - vts_array[0])` in `int`. With
`vts=8` and count 999999999 that is 8 * 999999998, past INT_MAX: signed overflow, undefined
behaviour. In practice the indent wraps (negative or wrong) before `trim_to_int` clamps it.

**How found:** the WP proof of `get_vts_sum` needs a precondition that the product fits in
int (`requires index <= a[0] || a[a[0]] * (index - a[0]) <= INT_MAX - 9999 * a[0]`); without it
the `signed_overflow` goals do not hold, and the callers above do not ensure it.

**Reproducer:** `vts-sum-overflow-repro.c` (verbatim functions + UBSan):
`runtime error: signed integer overflow: 8 * 999999998 cannot be represented in type 'int'`.
In Nvim (not run here, no Nvim build in this session):
`nvim --clean +'set sw=0 vts=8' +'call setline(1,"x")' +'exe "normal! V999999999>"'`.

**Fix:** verified_neovim branch `claude/project-thread-dvm5iw`, commit 09421b0: sum in
`int64_t` (callers already hold the indent in `int64_t` and clamp with `trim_to_int`).
The fixed `get_vts_sum` is proved with WP with no bound on `index`
(`FIXED=<fix checkout> bash register_ops/wp/run_wp.sh <upstream>`).

**Status:** open upstream; upstream issue draft in
`/mnt/project-files/neovim-verify/upstream/issue-ops-vts-sum-overflow.md` (not filed).
