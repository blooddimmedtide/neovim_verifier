-- nvim --clean -l search-csearch-overflow-repro.lua
-- Upstream: an ASan build reports global-buffer-overflow (WRITE of size 81) on the first
-- call; a normal build prints 81 and then the stale "x" + two composing chars.
-- Fixed: 31 (a + 15 whole composing chars, the most that fit in 32 bytes), then "x".
vim.fn.setcharsearch({ char = 'a' .. string.rep('\204\129', 40) })
print(#vim.fn.getcharsearch().char)
vim.fn.setcharsearch({ char = 'e\204\129\204\130' })
vim.fn.setcharsearch({ char = 'x' })
print(vim.inspect(vim.fn.getcharsearch().char))
