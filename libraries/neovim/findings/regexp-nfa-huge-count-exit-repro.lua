-- nvim --clean -l regexp-nfa-huge-count-exit-repro.lua
-- Upstream: "E41: Out of memory!" and Neovim exits (or the OOM killer stops it).
print(pcall(vim.fn.match, 'xx', [[\%#=2x\{3,15555555}]]))
print('still running')
