-- T6 value probe: Lua write taps on every config/names/ram.tsv row (size 0 -> 2 bytes) and every struct-field instance
-- (slot: 9 at FFD032+off+2*s; pairrec: FFD218+off); taps reinstalled every frame (cookbook C0012).
-- Per target: writes, value min/max, distinct set, writer pcs with counts, access sizes; targets <= 4 bytes and struct
-- fields also the first 256 value changes {frame, value}. Values normalised by tap mask (byte vs word).
-- Positive control: ram_frame_counter 0xFFC220 must take writes in the last 100 frames (ev=control pass|fail).
-- Writer pc is cpu PC at the tap, which may be ahead of the writing instruction.
-- Env: ORACLE_LIB/ORACLE_FRAMES set by scripts/oracle/mame.py (MAME 0.289); VALUES_SCEN = challenge|proleague|attract.
-- Run: VALUES_SCEN=<scen> PY scripts/oracle/mame.py run scripts/oracle/lua/values.lua --frames <scen frames> --tag t6_<scen>
local L = dofile(os.getenv("ORACLE_LIB"))
local LUADIR = os.getenv("ORACLE_LIB"):match("^(.*)/[^/]*$") or "."
local SCEN = os.getenv("VALUES_SCEN") or "attract"
local sc = assert(dofile(LUADIR .. "/scenarios.lua")[SCEN], "unknown VALUES_SCEN " .. SCEN)
local F = sc.frames
local cpu = manager.machine.devices[":maincpu"]
local sp = cpu.spaces["program"]
local pcst = cpu.state["PC"]
L.open()
local fields = {}
for _, port in pairs(manager.machine.ioport.ports) do
  for name, f in pairs(port.fields) do fields[name] = f end
end
local holds, level = {}, {}
for _, h in ipairs(sc.inputs) do
  if fields[h[2]] then holds[#holds + 1] = {h[2], h[1], h[1] + h[3]}; level[h[2]] = 0
  else L.emit{ev = "error", msg = "no field " .. h[2]} end
end
local function apply_inputs(n)
  local want = {}
  for name in pairs(level) do want[name] = 0 end
  for _, h in ipairs(holds) do if n >= h[2] and n < h[3] then want[h[1]] = 1 end end
  for name, v in pairs(want) do fields[name]:set_value(v); level[name] = v end
end

local function tsv(path)
  local rows, head = {}, nil
  for line in io.lines(path) do
    local c = {}
    for x in (line .. "\t"):gmatch("([^\t]*)\t") do c[#c + 1] = x end
    if not head then head = c
    else local r = {}; for i, k in ipairs(head) do r[k] = c[i] end; rows[#rows + 1] = r end
  end
  return rows
end

local CAP, SEQ = 4096, 256
local targets = {}
local function target(t)
  t.c, t.nd, t.dist, t.pcs, t.sz, t.seq = 0, 0, {}, {}, {}, {}
  targets[#targets + 1] = t
  return t
end
local rows, base, ctrl = {}, {}, nil
for _, r in ipairs(tsv("config/names/ram.tsv")) do
  local lo, sz = tonumber(r.addr), tonumber(r.size)
  local t = target{name = r.name, field = "-", addr = lo, size = sz, lo = lo, hi = lo + math.max(sz, 2) - 1,
                   small = sz <= 4}
  rows[#rows + 1] = t
  if r.struct ~= "-" then base[r.struct] = lo end
  if lo == 0xFFC220 then ctrl = t end
end
local inst = {}  -- word-aligned address -> struct-field instance target
for _, r in ipairs(tsv("config/names/structs.tsv")) do
  local off, sz = tonumber(r.offset), tonumber(r.size)
  local count = r.struct == "slot" and 9 or 1
  for s = 0, count - 1 do
    local a = base[r.struct] + off + 2 * s
    inst[a] = target{name = r.struct, field = r.struct .. "." .. r.field, inst = s, addr = a, size = sz,
                     lo = a, hi = a + sz - 1, small = true}
  end
end

local n = 0
local function rec(t, v, z, pc)
  t.c = t.c + 1
  if not t.mn or v < t.mn then t.mn = v end
  if not t.mx or v > t.mx then t.mx = v end
  if not t.dist[v] then
    if t.nd < CAP then t.dist[v] = true end
    t.nd = t.nd + 1
  end
  t.pcs[pc] = (t.pcs[pc] or 0) + 1
  t.sz[z] = true
  if t.small and v ~= t.last then
    if #t.seq < SEQ then t.seq[#t.seq + 1] = {n, v} end
    t.last = v
  end
end

-- merge row ranges into disjoint word-aligned tap ranges; each range dispatches to its rows and the instance map
local spans = {}
for _, t in ipairs(rows) do spans[#spans + 1] = {t.lo & ~1, t.hi | 1} end
table.sort(spans, function(a, b) return a[1] < b[1] end)
local merged = {}
for _, s in ipairs(spans) do
  local m = merged[#merged]
  if m and s[1] <= m[2] + 1 then m[2] = math.max(m[2], s[2]) else merged[#merged + 1] = {s[1], s[2]} end
end
local taps = {}
for i, m in ipairs(merged) do
  local list = {}
  for _, t in ipairs(rows) do if t.lo <= m[2] and t.hi >= m[1] then list[#list + 1] = t end end
  taps[#taps + 1] = sp:install_write_tap(m[1], m[2], "t6_values_" .. i, function(off, data, mask)
    local a, v, z
    if mask == 0xFF00 then a, v, z = off & ~1, (data >> 8) & 0xFF, 1
    elseif mask == 0x00FF then a, v, z = off | 1, data & 0xFF, 1
    else a, v, z = off & ~1, data & 0xFFFF, 2 end
    local e = a + z - 1
    local pc = pcst.value & 0xFFFFFF
    for _, t in ipairs(list) do if a <= t.hi and e >= t.lo then rec(t, v, z, pc) end end
    local t = inst[a & ~1]
    if t and a <= t.hi and e >= t.lo then rec(t, v, z, pc) end
  end)
end
L.emit{ev = "start", scen = SCEN, frames = F, taps = #taps, targets = #targets}

local ctrl_mark = 0
emu.register_frame_done(function()
  n = n + 1
  for _, t in ipairs(taps) do t:reinstall() end
  apply_inputs(n)
  if n == F - 100 then ctrl_mark = ctrl.c end
  if n < F then return end
  for _, t in ipairs(targets) do
    local d, p, s = nil, {}, {}
    if t.nd <= CAP then d = {}; for v in pairs(t.dist) do d[#d + 1] = v end; table.sort(d) end
    for pc, c in pairs(t.pcs) do p[#p + 1] = {pc, c} end
    table.sort(p, function(x, y) return x[2] > y[2] or (x[2] == y[2] and x[1] < y[1]) end)
    for i, x in ipairs(p) do p[i] = {L.hex(x[1]), x[2]} end
    for z in pairs(t.sz) do s[#s + 1] = z end
    table.sort(s)
    L.emit{ev = "t", name = t.name, field = t.field, inst = t.inst, addr = L.hex(t.addr), size = t.size, c = t.c,
           mn = t.mn, mx = t.mx, nd = t.nd, dist = d, pcs = p, sizes = s, seq = t.small and t.seq or nil}
  end
  local last = ctrl.c - ctrl_mark
  L.emit{ev = "control", addr = L.hex(ctrl.addr), total = ctrl.c, last100 = last, result = last > 0 and "pass" or "fail"}
  L.done{frames = n, scen = SCEN}
  manager.machine:exit()
end)
