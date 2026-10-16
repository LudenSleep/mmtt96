-- Boot probe: cold boot, then manager.machine:soft_reset(); per phase records the first executed PCs (trace of
-- one frame) and breakpoint hits on 0x000200 (entry), 0x015918 (Z80 upload), 0x00028C (last init insn, bra.s)
-- and the controls 0x000100 (header) and 0x00028E (init data table), which must never fire.
-- Env: ORACLE_LIB, ORACLE_OUT (JSONL), ORACLE_TRACE (trace file prefix), ORACLE_FRAMES (frames per phase, default 60). Writes {"ev":"done"} last.
-- MAME re-runs the autoboot script on soft_reset while earlier callbacks persist: the global guard keeps one instance.
if ORACLE_BOOT_LOADED then return end
ORACLE_BOOT_LOADED = true
local L = dofile(os.getenv("ORACLE_LIB"))
local PFX = os.getenv("ORACLE_TRACE")
local F = tonumber(os.getenv("ORACLE_FRAMES") or "60")
local BPS = {0x000200, 0x015918, 0x000100, 0x00028C, 0x00028E}
local HEAD = 64

L.open()
for _, a in ipairs(BPS) do L.bp(a) end

local function record(phase, mark, file)
  local raw = L.trace_pcs(file, HEAD)
  local hits = L.bp_hits(mark)
  local at = 1
  for i, pc in ipairs(raw) do
    if pc == "000000" then at = i break end
  end
  local pcs = {}
  for i = at, math.min(at + 7, #raw) do pcs[#pcs + 1] = raw[i] end
  local head = {}
  for i = 1, math.min(8, #raw) do head[i] = raw[i] end
  local h, names = {}, {}
  for _, a in ipairs(BPS) do h[#h + 1] = hits[a] or 0; names[#names + 1] = L.hex(a) end
  L.emit{ev = "phase", phase = phase, first_pcs = pcs, raw_head = head, pre_reset = at - 1,
         bp_addrs = names, bp_hits = h}
  os.remove(file)
end

local mark = L.mark()
L.trace_start(PFX .. "_cold.tr")
manager.machine.debugger:command("go")

local n = 0
emu.register_frame_done(function()
  n = n + 1
  if n == 1 or n == F + 1 then
    L.trace_stop()
  elseif n == F then
    record("cold", mark, PFX .. "_cold.tr")
    mark = L.mark()
    L.trace_start(PFX .. "_soft.tr")
    manager.machine:soft_reset()
  elseif n == 2 * F then
    record("soft", mark, PFX .. "_soft.tr")
    L.done{frames = n}
    manager.machine:exit()
  end
end)
