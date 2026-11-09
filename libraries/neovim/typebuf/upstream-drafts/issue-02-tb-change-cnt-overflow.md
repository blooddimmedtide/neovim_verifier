DRAFT, not filed. For Yerin to file at neovim/neovim (low severity; could be a PR instead).

Title: typebuf.tb_change_cnt wrap-around relies on signed overflow

`if (++typebuf.tb_change_cnt == 0) typebuf.tb_change_cnt = 1;` appears four times in
src/nvim/input.c (ins_typebuf, del_typebuf, alloc_typebuf, flush_buffers). The `== 0` test
expects wrap-around, but `++` on INT_MAX is undefined behavior for a signed int. Needs about
2^31 typeahead changes; not observed as a crash.

Suggested fix: `if (typebuf.tb_change_cnt == INT_MAX || ++typebuf.tb_change_cnt == 0) {`
