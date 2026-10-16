-- Coverage probe: records every executed maincpu PC over frames (ORACLE_FROM, ORACLE_FRAMES] of a run from cold boot.
-- Tracing is slow (~10-15 frames/s), so a long scenario runs as chunks of separate MAME calls: a chunk with
-- ORACLE_FROM > 0 loads save state ORACLE_LOAD on its first frame and starts tracing on the next, its frame counter
-- set to ORACLE_FROM; a chunk with ORACLE_SAVE saves state under that name at its last frame (exit one untraced frame
-- later). State and snapshot files live in the directory of ORACLE_TRACE (.run/oracle).
-- The trace runs in windows of ORACLE_WIN frames (default 20): each window's trace file is reduced to its unique PCs
-- (leading address field only) and deleted, so no raw trace outlives a window. At the end each unique PC gets its
-- instruction length from the debugger `dasm` command (address column only; next address - this address), and the
-- set is written to <ORACLE_TRACE>.pcs as "pc<TAB>len" hex lines (sorted). Addresses only; no bytes or mnemonics kept.
-- Inputs: ORACLE_INPUT = "frame:field:dur ..." (ioport field name, e.g. "P1 Start", held for frames [frame,
-- frame+dur) of the run; levels are re-applied every frame, so holds survive a chunk boundary);
-- ORACLE_SNAPS = "frame,frame,..." screen snapshots to <ORACLE_TRACE>_f<frame>.png.
-- Env: ORACLE_LIB, ORACLE_OUT, ORACLE_TRACE, ORACLE_FRAMES, ORACLE_FROM, ORACLE_LOAD, ORACLE_SAVE, ORACLE_WIN,
-- ORACLE_INPUT, ORACLE_SNAPS.
-- Emits {"ev":"input", frame, field, v} per input edge, {"ev":"snap", frame, file}, {"ev":"cover", from, frames,
-- windows, pcs, unknown_len, max_trace_bytes}, then {"ev":"done"}.
if ORACLE_COVERAGE_LOADED then return end
ORACLE_COVERAGE_LOADED = true
local L = dofile(os.getenv("ORACLE_LIB"))
local PFX = os.getenv("ORACLE_TRACE")
local F = tonumber(os.getenv("ORACLE_FRAMES") or "600")
local FROM = tonumber(os.getenv("ORACLE_FROM") or "0")
local LOAD, SAVE = os.getenv("ORACLE_LOAD"), os.getenv("ORACLE_SAVE")
local WIN = tonumber(os.getenv("ORACLE_WIN") or "20")
local TR = PFX .. "_w.tr"
local DA = PFX .. "_d.txt"
local dbg = manager.machine.debugger

L.open()
local fields = {}
for _, port in pairs(manager.machine.ioport.ports) do
  for name, f in pairs(port.fields) do fields[name] = f end
end
local holds, level = {}, {}
for fr, name, d in (os.getenv("ORACLE_INPUT") or ""):gmatch("(%d+):([^:]+):(%d+)") do
  name = name:gsub("^%s+", "")
  if not fields[name] then
    L.emit{ev = "error", msg = "no ioport field " .. name}
  else
    holds[#holds + 1] = {name, tonumber(fr), tonumber(fr) + tonumber(d)}
    level[name] = 0
  end
end
local function apply_inputs(n, force)
  local want = {}
  for name in pairs(level) do want[name] = 0 end
  for _, h in ipairs(holds) do
    if n >= h[2] and n < h[3] then want[h[1]] = 1 end
  end
  for name, v in pairs(want) do
    if v ~= level[name] or force then
      fields[name]:set_value(v)
      if v ~= level[name] then L.emit{ev = "input", frame = n, field = name, v = v} end
      level[name] = v
    end
  end
end
local snaps = {}
for fr in (os.getenv("ORACLE_SNAPS") or ""):gmatch("%d+") do snaps[tonumber(fr)] = true end
local dir = PFX:match("^(.*)/[^/]*$") or "."
manager.machine.options.entries["snapshot_directory"]:value(dir)
manager.machine.options.entries["state_directory"]:value(dir)
local base = PFX:match("([^/]*)$")

local seen, windows, maxb = {}, 0, 0
local function reduce()
  L.trace_stop()
  local f = io.open(TR, "r")
  if f then
    local size = f:seek("end")
    if size > maxb then maxb = size end
    f:seek("set", 0)
    local text = "\n" .. f:read("a")
    f:close()
    for a in text:gmatch("\n%s*(%x+):") do seen[a] = true end  -- string keys: hex text, converted in finish
  end
  os.remove(TR)
  windows = windows + 1
end

-- Instruction lengths: dasm each cluster of PCs (gaps <= 10 bytes) from its first PC; a PC the linear listing
-- skips (not an instruction start there) gets its own dasm.
local function dasm_lens(start, len, lens)
  dbg:command(string.format("dasm %s,%X,%X,0", DA, start, len))
  local prev
  for line in io.lines(DA) do
    local a = line:match("^%s*(%x+):")
    if a then
      a = tonumber(a, 16)
      if prev and lens[prev] == nil then lens[prev] = a - prev end
      prev = a
    end
  end
  os.remove(DA)
end

local function lengths(pcs)
  local lens = {}
  local i = 1
  while i <= #pcs do
    local j = i
    while j < #pcs and pcs[j + 1] - pcs[j] <= 10 do j = j + 1 end
    dasm_lens(pcs[i], pcs[j] - pcs[i] + 12, lens)
    i = j + 1
  end
  local unknown = 0
  for _, pc in ipairs(pcs) do
    if lens[pc] == nil or lens[pc] <= 0 then
      local one = {}
      dasm_lens(pc, 12, one)
      lens[pc] = one[pc]
      if lens[pc] == nil or lens[pc] <= 0 then unknown = unknown + 1 end
    end
  end
  return lens, unknown
end

local function finish(n)
  reduce()
  local uniq = {}
  for a in pairs(seen) do uniq[tonumber(a, 16) & 0xFFFFFF] = true end
  local pcs = {}
  for pc in pairs(uniq) do pcs[#pcs + 1] = pc end
  table.sort(pcs)
  local lens, unknown = lengths(pcs)
  local out = assert(io.open(PFX .. ".pcs", "w"))
  for _, pc in ipairs(pcs) do out:write(string.format("%06X\t%X\n", pc, lens[pc] or 0)) end
  out:close()
  L.emit{ev = "cover", from = FROM, frames = n, windows = windows, pcs = #pcs, unknown_len = unknown,
         max_trace_bytes = maxb}
  if SAVE then
    manager.machine:save(SAVE)  -- deferred to the end of this timeslice; exit one frame later
    return
  end
  L.done{frames = n}
  manager.machine:exit()
end

os.remove(TR)
local n, m, finished = FROM, 0, false
if FROM == 0 then L.trace_start(TR) end
emu.register_frame_done(function()
  if finished then
    L.done{frames = n, saved = SAVE}
    manager.machine:exit()
    return
  end
  if FROM > 0 and m == 0 then
    -- the load is deferred to the end of this timeslice; cold-boot PCs traced before it belong to the run anyway
    m = 1
    manager.machine:load(LOAD)
    apply_inputs(n, true)
    L.trace_start(TR)
    return
  end
  n = n + 1
  apply_inputs(n)
  if snaps[n] then
    local file = string.format("%s_f%05d.png", base, n)
    manager.machine.screens[":megadriv"]:snapshot(file)
    L.emit{ev = "snap", frame = n, file = file}
  end
  if n >= F then
    finished = true
    return finish(n)
  end
  if n % WIN == 0 then
    reduce()
    L.trace_start(TR)
  end
end)
dbg:command("go")
