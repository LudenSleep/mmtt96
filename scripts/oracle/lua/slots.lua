-- T4 slot probe: write census on ram_slottab/ram_pairrec (T4_WATCH, default FFD032:6C FFD218:14), bp hits (T4_BPS), mode word samples.
-- Env: ORACLE_LIB/ORACLE_FRAMES/ORACLE_INPUT/ORACLE_TRACE set by scripts/oracle/mame.py (MAME 0.289).
-- Run: PY scripts/oracle/mame.py run scripts/oracle/lua/slots.lua --frames N --tag t4_<scen> (inputs: see .run/t4/scen.sh challenge|proleague|attract).
local L = dofile(os.getenv("ORACLE_LIB"))
local F = tonumber(os.getenv("ORACLE_FRAMES") or "600")
local dbg = manager.machine.debugger
local space = manager.machine.devices[":maincpu"].spaces["program"]
L.open()
local fields = {}
for _, port in pairs(manager.machine.ioport.ports) do
  for name, f in pairs(port.fields) do fields[name] = f end
end
local holds, level = {}, {}
for fr, name, d in (os.getenv("ORACLE_INPUT") or ""):gmatch("(%d+):([^:]+):(%d+)") do
  name = name:gsub("^%s+", "")
  if fields[name] then holds[#holds + 1] = {name, tonumber(fr), tonumber(fr) + tonumber(d)}; level[name] = 0
  else L.emit{ev = "error", msg = "no field " .. name} end
end
local function apply_inputs(n)
  local want = {}
  for name in pairs(level) do want[name] = 0 end
  for _, h in ipairs(holds) do if n >= h[2] and n < h[3] then want[h[1]] = 1 end end
  for name, v in pairs(want) do fields[name]:set_value(v); level[name] = v end
end
for a in (os.getenv("T4_BPS") or ""):gmatch("%x+") do L.bp(tonumber(a, 16)) end
for wlo, wlen in (os.getenv("T4_WATCH") or "FFD032:6C FFD218:14"):gmatch("(%x+):(%x+)") do
  dbg:command(string.format('wpset %s,%s,w,1,{printf "SW %%X %%X %%X",wpaddr,wpsize,pc ; go}', wlo, wlen))
end
local PFX = os.getenv("ORACLE_TRACE")
local dir = PFX:match("^(.*)/[^/]*$") or "."
manager.machine.options.entries["snapshot_directory"]:value(dir)
local snaps = {}
for fr in (os.getenv("ORACLE_SNAPS") or ""):gmatch("%d+") do snaps[tonumber(fr)] = true end
local mark, n = L.mark(), 0
local W, BP, modes = {}, {}, {}
local lastmode
emu.register_frame_done(function()
  n = n + 1
  apply_inputs(n)
  local log = dbg.consolelog
  for i = mark + 1, #log do
    local s = tostring(log[i])
    local a, z, pc = s:match("^SW (%x+) (%x+) (%x+)$")
    if a then
      local k = string.format("%06X|%d|%06X", tonumber(a,16) & 0xFFFFFF, tonumber(z,16)//8, tonumber(pc,16) & 0xFFFFFF)
      local w = W[k]; if not w then w = {c = 0, f = n}; W[k] = w end
      w.c = w.c + 1; w.l = n
    end
    local b = s:match("BPHIT (%x+)")
    if b then local e = BP[b]; if not e then e = {c = 0, f = n}; BP[b] = e end; e.c = e.c + 1 end
  end
  mark = #log
  local m = space:read_u16(0xFFE69A)
  if m ~= lastmode then L.emit{ev = "mode", frame = n, v = m}; lastmode = m end
  if snaps[n] then manager.machine.screens[":megadriv"]:snapshot(string.format("t4_f%d.png", n)) end
  if n % 300 == 0 then
    local t = {}
    for a = 0xFFD032, 0xFFD056, 2 do t[#t + 1] = space:read_u16(a) end
    L.emit{ev = "snap", frame = n, xy = t}
  end
  if n < F then return end
  for k, w in pairs(W) do L.emit{ev = "w", key = k, c = w.c, f = w.f, l = w.l} end
  for b, e in pairs(BP) do L.emit{ev = "bp", addr = b, c = e.c, f = e.f} end
  L.done()
  manager.machine:exit()
end)
