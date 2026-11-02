-- nvim --clean -l regexp-nfa-backslash-multibyte-repro.lua
-- Upstream: engine 1 finds "é", engine 2 finds nothing. Fixed: both find it.
for e = 1, 2 do
  print('engine ' .. e, vim.inspect(vim.fn.matchstrpos('xéy', [[\%#=]] .. e .. [[\é]])))
end
