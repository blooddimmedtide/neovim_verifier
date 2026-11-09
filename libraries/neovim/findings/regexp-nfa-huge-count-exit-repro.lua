-- nvim --clean -l regexp-nfa-huge-count-exit-repro.lua
-- Upstream: "E41: Out of memory!" and Neovim exits (or the OOM killer stops it).
-- Fixed: "true -1" twice (two x's are fewer than the minimum) and "still running".
print(pcall(vim.fn.match, 'xx', [[\%#=2x\{3,15555555}]]))
print(pcall(vim.fn.match, 'xx', [[x\{300,15555555}]]))   -- default engine
print('still running')
