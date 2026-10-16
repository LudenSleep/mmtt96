-- 1.9 T1 scenario driver: scripted pad inputs (no GUI), mode-word sequence, snapshots, save/load states, RAM pokes.
-- Scenario from scripts/oracle/lua/scenarios.lua by env SCEN (fields frames, inputs, load, save, snaps, pokes);
-- env adds to it: SCEN_INPUT "frame:field:hold ..." (e.g. "40:P1 Start:5 90:P1 Down:4"), SCEN_LOAD <state>,
-- SCEN_SAVE "frame:name ...", SCEN_SNAPS "frame ..." or "every:N", SCEN_POKES "frame:addr:bytes:value ..." (hex addr/value),
-- SCEN_PEEK "addr:len ..." (hex) emits RAM words at each snapshot frame (ev=peek; exploration, .run/ only),
-- SCEN_FIELDS=1 emits the ioport field names once (ev=fields).
-- Frames count from 1 after start (after the state load when SCEN_LOAD/load is set).
-- States: .run/states/<name> (MAME state files; ignored). Snapshots: .run/oracle/<run_id>/<scen>_f<frame>.png (ignored).
-- Events: mode {frame, v} on every change of the mode word ram_FFE69A (u16), poke, save, snap, done {modes}.
-- Hooks: a probe sets globals DRIVE_HOOK(n, L) (every counted frame, after pokes/saves) and DRIVE_DONE(n, L), then dofiles this.
-- Run: SCEN=<id> PY scripts/oracle/mame.py run scripts/oracle/lua/drive.lua --frames <n> --tag t1_<id> [--secs S]
local L = dofile(os.getenv("ORACLE_LIB"))
local LUADIR = os.getenv("ORACLE_LIB"):match("^(.*)/[^/]*$") or "."
local SCEN = os.getenv("SCEN") or "attract"
local sc = dofile(LUADIR .. "/scenarios.lua")[SCEN] or {frames = 600, inputs = {}}
local F = tonumber(os.getenv("ORACLE_FRAMES") or "0")
if F <= 0 then F = sc.frames end
local machine = manager.machine
local space = machine.devices[":maincpu"].spaces["program"]
local opts = machine.options.entries
local PFX = os.getenv("ORACLE_TRACE")
opts["snapshot_directory"]:value(PFX)
opts["state_directory"]:value(".run/states")
L.open()

local fields, names = {}, {}
for _, port in pairs(machine.ioport.ports) do
  for name, f in pairs(port.fields) do fields[name] = f; names[#names + 1] = name end
end
table.sort(names)
if os.getenv("SCEN_FIELDS") == "1" then L.emit{ev = "fields", names = names} end

local inputs = {}
for _, h in ipairs(sc.inputs or {}) do inputs[#inputs + 1] = h end
for fr, name, d in (os.getenv("SCEN_INPUT") or ""):gmatch("(%d+):([^:]+):(%d+)") do
  inputs[#inputs + 1] = {tonumber(fr), (name:gsub("^%s+", "")), tonumber(d)}
end
local holds, level = {}, {}
for _, h in ipairs(inputs) do
  if fields[h[2]] then holds[#holds + 1] = {h[2], h[1], h[1] + h[3]}; level[h[2]] = 0
  else L.emit{ev = "error", msg = "no field " .. h[2]} end
end
local function apply_inputs(n)
  local want = {}
  for name in pairs(level) do want[name] = 0 end
  for _, h in ipairs(holds) do if n >= h[2] and n < h[3] then want[h[1]] = 1 end end
  for name, v in pairs(want) do fields[name]:set_value(v); level[name] = v end
end

local saves, snaps, every, pokes = {}, {}, nil, {}
for _, s in ipairs(sc.save or {}) do saves[s[1]] = s[2] end
for fr, name in (os.getenv("SCEN_SAVE") or ""):gmatch("(%d+):([%w_]+)") do saves[tonumber(fr)] = name end
for _, f in ipairs(sc.snaps or {}) do snaps[f] = true end
local sn = os.getenv("SCEN_SNAPS") or ""
every = tonumber(sn:match("^every:(%d+)") or "")
for fr in sn:gmatch("%f[%w](%d+)") do if not every then snaps[tonumber(fr)] = true end end
for _, p in ipairs(sc.pokes or {}) do pokes[#pokes + 1] = p end
for fr, a, b, v in (os.getenv("SCEN_POKES") or ""):gmatch("(%d+):(%x+):(%d):(%x+)") do
  pokes[#pokes + 1] = {tonumber(fr), tonumber(a, 16), tonumber(b), tonumber(v, 16)}
end

local load = os.getenv("SCEN_LOAD") or sc.load
local n, started, lastmode, modes = 0, load == nil, nil, {}
if load then machine:load(load) end
local skip = 2  -- frames to let a scheduled state load land before counting
emu.register_frame_done(function()
  if not started then
    skip = skip - 1
    if skip > 0 then return end
    started = true
    L.emit{ev = "loaded", state = load}
  end
  n = n + 1
  apply_inputs(n)
  for _, p in ipairs(pokes) do
    if p[1] == n then
      if p[3] == 1 then space:write_u8(p[2], p[4]) elseif p[3] == 2 then space:write_u16(p[2], p[4])
      else space:write_u32(p[2], p[4]) end
      L.emit{ev = "poke", frame = n, addr = L.hex(p[2]), bytes = p[3], v = p[4]}
    end
  end
  local m = space:read_u16(0xFFE69A)
  if m ~= lastmode then
    L.emit{ev = "mode", frame = n, v = string.format("%04X", m)}
    modes[#modes + 1] = string.format("%04X@%d", m, n)
    lastmode = m
  end
  if snaps[n] or (every and n % every == 0) then
    machine.screens[":megadriv"]:snapshot(string.format("%s_f%05d.png", SCEN, n))
    L.emit{ev = "snap", frame = n}
    for a, len in (os.getenv("SCEN_PEEK") or ""):gmatch("(%x+):(%x+)") do  -- exploration only; stays in .run/
      local t, lo = {}, tonumber(a, 16)
      for x = lo, lo + tonumber(len, 16) - 1, 2 do t[#t + 1] = string.format("%04X", space:read_u16(x)) end
      L.emit{ev = "peek", frame = n, addr = a, w = t}
    end
  end
  if saves[n] then machine:save(saves[n]); L.emit{ev = "save", frame = n, state = saves[n]} end
  if DRIVE_HOOK then DRIVE_HOOK(n, L) end  -- probe scripts that dofile this driver (writers.lua, probe.lua, T2)
  if n < F then return end
  if DRIVE_DONE then DRIVE_DONE(n, L) end
  L.done{scen = SCEN, frames = n, modes = modes}
  machine:exit()
end)
