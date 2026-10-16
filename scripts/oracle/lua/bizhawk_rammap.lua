-- BizHawk 2.11 (GPGX) RAM-map probe, second oracle for rammap.lua: hard reset, then ORACLE_FRAMES frames of attract
-- with no input; emits {"ev":"fact", key, value} lines with the same keys/format as rammap.lua.
-- Facts (addresses as 6-digit hex; `none` when never observed):
--   entry_after_trap       first 68K PC after the reset trap: the exec-any callback (M68K BUS) first reports 000000
--                          (reset trap, as MAME's trace does); the next exec address is the entry (same rule as
--                          mame.boot_rows); `-` if the first address is not 000000. First 8 addresses go to `stat`
--   z80_sha1_after_upload  Z80 RAM (domain `Z80 RAM`) 0x0000 + 0x146C dumped by an exec callback at 0x01593E (first
--                          insn after the upload loop, before the Z80 is released); first hit only. Emitted as
--                          file:<path>:<size>; the host (mame.fact_rows) replaces it with the sha1
--   frame_counter          68K RAM longs (even addresses) whose value grew by exactly 1 every frame from frame
--                          SCAN_FROM to the last frame (scan over all of 0xFF0000-0xFFFFFF), comma-joined
-- Gotcha: the script starts after frame 1 has run (framecount 1), so it calls client.reboot_core() first (hard
-- reset, framecount 0, the script survives) and registers the callbacks after it: reboot_core drops callbacks
-- registered before it (both facts read `none` when registered first).
-- Env: ORACLE_OUT, ORACLE_TRACE (absolute prefix), ORACLE_FRAMES. Writes {"ev":"done"} last, then client.exit().
-- Addresses and sizes only; never ROM bytes or disassembly.
local OUT = os.getenv("ORACLE_OUT")
local PFX = os.getenv("ORACLE_TRACE")
local F = tonumber(os.getenv("ORACLE_FRAMES") or "600")
local Z80FILE = PFX .. "_z80.bin"
local Z80UP, Z80LEN = 0x01593E, 0x146C
local SCAN_FROM = math.min(60, F - 1)
local BUS, RAM, ZRAM = "M68K BUS", "68K RAM", "Z80 RAM"

local out = assert(io.open(OUT, "w"))
local function emit(obj)  -- flat object, string/integer values, keys sorted
  local keys, parts = {}, {}
  for k in pairs(obj) do keys[#keys + 1] = k end
  table.sort(keys)
  for i, k in ipairs(keys) do
    local v = obj[k]
    parts[i] = '"' .. k .. '":' .. (type(v) == "number" and string.format("%d", v) or ('"' .. tostring(v) .. '"'))
  end
  out:write("{" .. table.concat(parts, ",") .. "}\n")
  out:flush()
end
local function hex(n) return string.format("%06X", n & 0xFFFFFF) end

pcall(client.speedmode, 6400)
pcall(client.invisibleemulation, true)

local fc_before = emu.framecount()
client.reboot_core()
local fc_after = emu.framecount()

local pcs, z80 = {}, false
local any_id = event.onmemoryexecuteany(function(addr)
  if #pcs < 8 then pcs[#pcs + 1] = addr end
end, "bh_first_pcs", BUS)
event.onmemoryexecute(function()
  if z80 then return end
  z80 = true
  local b = memory.read_bytes_as_array(0, Z80LEN, ZRAM)
  local f = assert(io.open(Z80FILE, "wb"))
  for i = 1, #b, 1024 do f:write(string.char(table.unpack(b, i, math.min(i + 1023, #b)))) end
  f:close()
end, Z80UP, "bh_z80up", BUS)

local cand, n = nil, 0
while n < F do
  emu.frameadvance()
  n = n + 1
  if #pcs >= 8 and any_id then
    event.unregisterbyid(any_id)
    any_id = nil
  end
  if n == SCAN_FROM then
    cand = {}
    for a = 0, 0xFFFC, 2 do cand[a] = memory.read_u32_be(a, RAM) end
  elseif cand then
    for a, prev in pairs(cand) do
      local v = memory.read_u32_be(a, RAM)
      cand[a] = ((v - prev) & 0xFFFFFFFF) == 1 and v or nil
    end
  end
end

local fc = {}
for a in pairs(cand or {}) do fc[#fc + 1] = a end
table.sort(fc)
for i, a in ipairs(fc) do fc[i] = hex(0xFF0000 + a) end
local zsize = 0
if z80 then
  local f = io.open(Z80FILE, "rb")
  if f then zsize = #f:read("a"); f:close() end
end
local facts = {
  entry_after_trap = #pcs == 0 and "none" or (pcs[1] == 0 and pcs[2] and hex(pcs[2]) or "-"),
  z80_sha1_after_upload = zsize > 0 and string.format("file:%s:%d", Z80FILE, zsize) or "none",
  frame_counter = #fc > 0 and table.concat(fc, ",") or "none",
}
local keys = {}
for k in pairs(facts) do keys[#keys + 1] = k end
table.sort(keys)
for _, k in ipairs(keys) do emit{ev = "fact", key = k, value = facts[k]} end
local head = {}
for i, a in ipairs(pcs) do head[i] = hex(a) end
emit{ev = "stat", first_pcs = table.concat(head, ","), framecount_before_reset = fc_before, framecount_after_reset = fc_after, frames = n,
     framecount_end = emu.framecount()}
emit{ev = "done", frames = n}
out:close()
client.exit()
