-- nvim --clean -l regexp-bt-position-wrap-repro.lua
-- Upstream: engine 1 matches "a" in line 1 (4294967297 wrapped to 1); engine 2 gives E951.
-- Fixed: both give E951.
for e = 1, 2 do
  local ok, r = pcall(vim.fn.match, 'a', [[\%#=]] .. e .. [[\%4294967297l]])
  print('engine ' .. e, ok and ('match at ' .. r) or r)
end
