-- Oracle Lua helpers for MAME 0.289 (-debug -debugger none): JSONL writer, trace and breakpoint helpers.
-- Loaded by the probe scripts with dofile(os.getenv("ORACLE_LIB")); output path from env ORACLE_OUT.
-- Records PCs/addresses only; never writes ROM bytes or disassembly text.
local M = {}

local function jval(v)
  local t = type(v)
  if t == "number" then
    return math.type(v) == "integer" and string.format("%d", v) or string.format("%.17g", v)
  elseif t == "boolean" then
    return v and "true" or "false"
  elseif t == "table" then
    local parts = {}
    for i = 1, #v do parts[i] = jval(v[i]) end
    return "[" .. table.concat(parts, ",") .. "]"
  elseif v == nil then
    return "null"
  end
  return '"' .. tostring(v):gsub('[%c"\\]', function(c) return string.format("\\u%04x", c:byte()) end) .. '"'
end

-- JSONL writer: M.open(path); M.emit{ev="x", ...} writes one object per line (keys sorted).
function M.open(path)
  M.f = assert(io.open(path or os.getenv("ORACLE_OUT"), "w"))
end

function M.emit(obj)
  local keys = {}
  for k in pairs(obj) do keys[#keys + 1] = k end
  table.sort(keys)
  local parts = {}
  for i, k in ipairs(keys) do parts[i] = jval(k) .. ":" .. jval(obj[k]) end
  M.f:write("{" .. table.concat(parts, ",") .. "}\n")
  M.f:flush()
end

function M.done(extra)
  local obj = extra or {}
  obj.ev = "done"
  M.emit(obj)
  M.f:close()
end

function M.hex(n) return string.format("%06X", n) end

local dbg = manager.machine.debugger

-- Trace the main CPU into file (noloop); stop with M.trace_stop().
function M.trace_start(file)
  dbg:command("trace " .. file .. ",maincpu,noloop")
end

function M.trace_stop()
  dbg:command("trace off,maincpu")
end

-- First n PCs (hex strings) of a trace file: only the leading address field of each line is kept.
function M.trace_pcs(file, n)
  local pcs = {}
  local f = io.open(file, "r")
  if not f then return pcs end
  for line in f:lines() do
    local a = line:match("^%s*(%x+):")
    if a then
      pcs[#pcs + 1] = string.format("%06X", tonumber(a, 16))
      if #pcs >= n then break end
    end
  end
  f:close()
  return pcs
end

-- Breakpoint that logs "BPHIT <addr>" to the debugger console and resumes. The address is baked into the
-- text: on the m68000 core the `pc` symbol reads insn+2 at the hit (0x000200 printed 202).
function M.bp(addr)
  dbg:command(string.format('bpset %X,1,{printf "BPHIT %X" ; go}', addr, addr))
end

-- Console log length now (mark) and the set of BPHIT addresses logged since mark: {[addr]=count}.
function M.mark()
  return #dbg.consolelog
end

function M.bp_hits(mark)
  local hits = {}
  local log = dbg.consolelog
  for i = mark + 1, #log do
    local a = tostring(log[i]):match("BPHIT (%x+)")
    if a then
      a = tonumber(a, 16)
      hits[a] = (hits[a] or 0) + 1
    end
  end
  return hits
end

return M
