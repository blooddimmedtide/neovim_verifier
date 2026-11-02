-- nvim --clean -l regexp-getdecchrs-overflow-repro.lua
-- Upstream: 18446744073709551681 wraps to 65 ('A'), so the pattern matches "A" (and a
-- UBSan build reports the signed overflow). Fixed: E678 for both engines.
for e = 1, 2 do
  local ok, r = pcall(vim.fn.match, 'A', [[\%#=]] .. e .. [[\%d18446744073709551681]])
  print('engine ' .. e, ok and ('match at ' .. r) or r)
end
