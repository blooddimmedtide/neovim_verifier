-- nvim --clean -l regexp-bt-composing-atom-repro.lua
-- Engine 1 matches "á" although the pattern needs a following "q"; engine 2 does not match.
local acute = '\204\129'   -- U+0301 COMBINING ACUTE ACCENT
for e = 1, 2 do
  print('engine ' .. e, vim.inspect(vim.fn.matchstrpos('a' .. acute .. '~', [[\%#=]] .. e .. acute .. 'q')))
end
