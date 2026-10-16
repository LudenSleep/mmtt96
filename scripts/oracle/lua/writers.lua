-- 1.9 T2 writer probe: who writes what, per frame. Runs under drive.lua (SCEN, SCEN_LOAD, SCEN_INPUT, SCEN_POKES...).
-- RAM: write taps on WATCH ranges "addr:len ..." (hex); controls always added: FFC220:2 (ram_frame_counter, positive:
--   written every frame) and 000100:2 (ROM header, negative: never written; 000000 is written once in boot runs). Writes counted per word per writer pc per frame.
-- VDP: control port C00004-7 write tap: register-set words (10rrrrrr vvvvvvvv -> reg number, value) and two-word access
--   commands (target VRAM/CRAM/VSRAM, read/write, 16-bit address, DMA flag); a control-port read drops a pending first
--   word; data port C00000-3 writes counted per command (dw). Taps reinstalled every frame (cookbook C0012).
-- Writer pc = cpu PC at the tap; may be ahead of the writing instruction (C0015).
-- Series (game-derived; ignored .run/ only), prefix P = ORACLE_OUT minus .jsonl:
--   P_writes.tsv  frame addr pc count       (RAM words)
--   P_vdp.tsv     frame kind pc a b dma dw  (kind reg: a=reg b=value; kind cmd: a=target b=address)
--   P_series.tsv  frame slottab pairrec     (ram_slottab FFD032+6C, ram_pairrec FFD218+14, hex bytes)
-- Aggregate: PY scripts/oracle/writers_agg.py <run>...
-- Run: SCEN=<id> SCEN_LOAD=<state> WATCH="FFD164:12" PY scripts/oracle/mame.py run scripts/oracle/lua/writers.lua
--      --frames <n> --secs 900 --tag t2w_<id>
local LUADIR = os.getenv("ORACLE_LIB"):match("^(.*)/[^/]*$") or "."
local cpu = manager.machine.devices[":maincpu"]
local sp = cpu.spaces["program"]
local pcst = cpu.state["PC"]
local P = os.getenv("ORACLE_OUT"):gsub("%.jsonl$", "")
local fw = assert(io.open(P .. "_writes.tsv", "w"))
local fv = assert(io.open(P .. "_vdp.tsv", "w"))
local fs = assert(io.open(P .. "_series.tsv", "w"))
fw:write("frame\taddr\tpc\tcount\n")
fv:write("frame\tkind\tpc\ta\tb\tdma\tdw\n")
fs:write("frame\tslottab\tpairrec\n")

local rec = false            -- recording starts after the first counted frame (taps then fire inside a known frame)
local ram = {}               -- word addr -> pc -> count, this frame
local vdp = {}               -- this frame's VDP records
local pend, cmd = nil, nil   -- pending first command word; current access command record
local TGT = {[0x1] = "vram", [0x3] = "cram", [0x5] = "vsram", [0x0] = "vram_r", [0x8] = "cram_r", [0x4] = "vsram_r"}

local function pc() return pcst.value & 0xFFFFFF end

local taps, watch = {}, {}
local spec = "FFC220:2 000100:2 " .. (os.getenv("WATCH") or "")
for a, len in spec:gmatch("(%x+):(%x+)") do
  local lo = tonumber(a, 16)
  local hi = lo + tonumber(len, 16) - 1
  watch[#watch + 1] = {lo = lo, hi = hi}
  taps[#taps + 1] = sp:install_write_tap(lo & ~1, hi | 1, "t2_watch_" .. #taps, function(off, data, mask)
    if not rec then return end
    local w, p = off & ~1, pc()
    local t = ram[w]
    if not t then t = {}; ram[w] = t end
    t[p] = (t[p] or 0) + 1
  end)
end

taps[#taps + 1] = sp:install_write_tap(0xC00004, 0xC00007, "t2_vdp_ctrl", function(off, data, mask)
  if not rec then return end
  local w = data & 0xFFFF
  if pend then
    local cd = ((pend >> 14) & 3) | ((w >> 2) & 0x3C)
    local a = (pend & 0x3FFF) | ((w & 3) << 14)
    cmd = {"cmd", pc(), TGT[cd & 0xF] or string.format("cd%X", cd & 0xF), a, (cd & 0x20) ~= 0 and 1 or 0, 0}
    vdp[#vdp + 1] = cmd
    pend = nil
  elseif (w & 0xC000) == 0x8000 then
    vdp[#vdp + 1] = {"reg", pc(), (w >> 8) & 0x1F, w & 0xFF, 0, 0}
  else
    pend = w
  end
end)
taps[#taps + 1] = sp:install_read_tap(0xC00004, 0xC00007, "t2_vdp_stat", function(off, data, mask)
  pend = nil
end)
taps[#taps + 1] = sp:install_write_tap(0xC00000, 0xC00003, "t2_vdp_data", function(off, data, mask)
  if rec and cmd then cmd[6] = cmd[6] + 1 end
end)

local function hex(s) return (s:gsub(".", function(c) return string.format("%02X", c:byte()) end)) end

DRIVE_HOOK = function(n, L)
  if rec then  -- flush what frame n wrote
    local ws = {}
    for w in pairs(ram) do ws[#ws + 1] = w end
    table.sort(ws)
    for _, w in ipairs(ws) do
      local ps = {}
      for p in pairs(ram[w]) do ps[#ps + 1] = p end
      table.sort(ps)
      for _, p in ipairs(ps) do fw:write(string.format("%d\t%06X\t%06X\t%d\n", n, w, p, ram[w][p])) end
    end
    for _, r in ipairs(vdp) do
      if r[1] == "reg" then fv:write(string.format("%d\treg\t%06X\t%02X\t%02X\t0\t0\n", n, r[2], r[3], r[4]))
      else fv:write(string.format("%d\tcmd\t%06X\t%s\t%04X\t%d\t%d\n", n, r[2], r[3], r[4], r[5], r[6])) end
    end
    fs:write(string.format("%d\t%s\t%s\n", n, hex(sp:read_range(0xFFD032, 0xFFD09D, 8)),
                           hex(sp:read_range(0xFFD218, 0xFFD22B, 8))))
  end
  ram, vdp, rec = {}, {}, true
  for _, t in ipairs(taps) do t:reinstall() end
end

DRIVE_DONE = function(n, L)
  fw:close(); fv:close(); fs:close()
  local w = {}
  for _, x in ipairs(watch) do w[#w + 1] = string.format("%06X:%X", x.lo, x.hi - x.lo + 1) end
  L.emit{ev = "writers", watch = w, series = P}
end

assert(loadfile(LUADIR .. "/drive.lua", "t", _ENV))()  -- same env: drive.lua sees DRIVE_HOOK/DRIVE_DONE
