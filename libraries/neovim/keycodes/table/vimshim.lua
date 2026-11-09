vim = {}
function vim.deepcopy(t) if type(t) ~= 'table' then return t end local r = {} for k, v in pairs(t) do r[k] = vim.deepcopy(v) end return r end
function vim.tbl_keys(t) local r = {} for k in pairs(t) do r[#r + 1] = k end return r end
function vim.tbl_values(t) local r = {} for _, v in pairs(t) do r[#r + 1] = v end return r end
function vim.tbl_isempty(t) return next(t) == nil end
function vim.list_extend(d, s) for _, v in ipairs(s) do d[#d + 1] = v end return d end
function vim.iter(t) return { all = function(_, f) for _, v in ipairs(t) do if not f(v) then return false end end return true end } end
