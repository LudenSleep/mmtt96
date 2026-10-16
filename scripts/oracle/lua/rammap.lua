-- RAM-map probe: cold boot into attract (no input) for ORACLE_FRAMES frames; emits {"ev":"fact", key, value} lines.
-- Facts (addresses as 6-digit hex; `none` when never observed):
--   z80_sha1_after_upload  sha1 of Z80 RAM 0xA00000 + 0x146C saved by a bp at 0x01593E (first insn after the upload
--                          loop at 0x015938, before the Z80 is released); first hit only. Emitted as
--                          file:<path>:<size>; the host (mame.fact_rows) replaces it with the sha1
--   ssp_after_init         sp at the bp on 0x000308 (first insn after the post-init entry 0x0002FA loads sp; at the
--                          last init insn 0x00028C sp still holds the vector-0 value)
--   irq6_entry/irq4_entry  vector-30/28 handler address (0x01F96A/0x01F964) if its entry bp fired, else none
--   irq6_writes/irq4_writes work-RAM write range min-max (inclusive) while inside the handler: flag set at the entry bp,
--                          cleared at its rte bp (0x01FA2C/0x01F968); census by a write watchpoint on 0xFF0000-0xFFFFFF;
--                          stack writes (address >= current sp - 0x40) are counted apart, not in the range
--   frame_counter          work-RAM byte/word/long written inside the IRQ6 handler whose value at every frame end advanced
--                          by exactly the IRQ6 count of that frame (from its first write on), widest interval kept, comma-joined
--   jcart_reads            sorted set of 0x380000-0x3FFFFF addresses read (read watchpoint), comma-joined
--   pad_reads              sorted set of pad-port read addresses in 0xA10002-0xA10005 (positive control)
-- Env: ORACLE_LIB, ORACLE_OUT, ORACLE_TRACE, ORACLE_FRAMES. Writes {"ev":"done"} last. Addresses only.
if ORACLE_RAMMAP_LOADED then return end
ORACLE_RAMMAP_LOADED = true
local L = dofile(os.getenv("ORACLE_LIB"))
local PFX = os.getenv("ORACLE_TRACE")
local F = tonumber(os.getenv("ORACLE_FRAMES") or "600")
local Z80FILE = PFX .. "_z80.bin"
local IRQ = {[6] = {entry = 0x01F96A, rte = 0x01FA2C, flag = "temp6"}, [4] = {entry = 0x01F964, rte = 0x01F968, flag = "temp4"}}
local dbg = manager.machine.debugger
local space = manager.machine.devices[":maincpu"].spaces["program"]

local function a24(s) return tonumber(s, 16) & 0xFFFFFF end

L.open()
os.remove(Z80FILE)
dbg:command("temp1=0")
dbg:command(string.format('bpset 1593E,temp1==0,{temp1=1 ; save %s,a00000,146c ; printf "Z80UP" ; go}', Z80FILE))
dbg:command('bpset 308,1,{printf "SSP %X",sp ; go}')
for k, h in pairs(IRQ) do
  dbg:command(h.flag .. "=0")
  dbg:command(string.format('bpset %X,1,{%s=1 ; printf "IE%d" ; go}', h.entry, h.flag, k))
  dbg:command(string.format('bpset %X,1,{%s=0 ; go}', h.rte, h.flag))
  dbg:command(string.format('wpset FF0000,10000,w,%s==1,{printf "W%d %%X %%X %%X",wpaddr,wpsize,sp ; go}', h.flag, k))
end
dbg:command('wpset 380000,80000,r,1,{printf "JR %X",wpaddr ; go}')
dbg:command('wpset A10002,4,r,1,{printf "PR %X",wpaddr ; go}')

local st = {ssp = nil, z80 = false, hits = {[6] = 0, [4] = 0}, lo = {}, hi = {}, jr = {}, pr = {}, writes = 0, stack = 0}
local cand = {}  -- [addr|size] = {addr, size, prev, ok}
local mark, n = L.mark(), 0

local function set_str(s)
  local t = {}
  for a in pairs(s) do t[#t + 1] = a end
  if #t == 0 then return "none" end
  table.sort(t)
  for i, a in ipairs(t) do t[i] = L.hex(a) end
  return table.concat(t, ",")
end

local function read(addr, size)
  if size == 1 then return space:read_u8(addr) elseif size == 2 then return space:read_u16(addr) end
  return space:read_u32(addr)
end

emu.register_frame_done(function()
  n = n + 1
  local log = dbg.consolelog
  local fh = {[6] = 0, [4] = 0}
  for i = mark + 1, #log do
    local s = tostring(log[i])
    local k = s:match("^IE(%d)$")
    if k then k = tonumber(k); fh[k] = fh[k] + 1 end
    local wk, wa, wz, wsp = s:match("^W(%d) (%x+) (%x+) (%x+)$")
    if wk then
      wk, wa, wz = tonumber(wk), a24(wa), tonumber(wz, 16) // 8  -- wpsize is in bits
      st.writes = st.writes + 1
    end
    if wk and wa >= a24(wsp) - 0x40 then  -- stack: within a movem/exception-frame window of the current sp
      st.stack = st.stack + 1
    elseif wk then
      local e = wa + wz - 1
      if not st.lo[wk] or wa < st.lo[wk] then st.lo[wk] = wa end
      if not st.hi[wk] or e > st.hi[wk] then st.hi[wk] = e end
      if wk == 6 then
        for _, z in ipairs(wz == 2 and wa % 2 == 0 and {2, 4} or {wz}) do
          local key = wa .. "|" .. z
          if not cand[key] then cand[key] = {addr = wa, size = z, ok = true, new = true} end
        end
      end
    end
    local j = s:match("^JR (%x+)$")
    if j then st.jr[a24(j)] = true end
    local p = s:match("^PR (%x+)$")
    if p then st.pr[a24(p)] = true end
    local sp = s:match("^SSP (%x+)$")
    if sp and not st.ssp then st.ssp = a24(sp) end
    if s == "Z80UP" then st.z80 = true end
  end
  mark = #log
  st.hits[6], st.hits[4] = st.hits[6] + fh[6], st.hits[4] + fh[4]
  for _, c in pairs(cand) do
    local v = read(c.addr, c.size)
    if c.new then
      c.new = nil
    elseif c.ok then
      local mask = (1 << (8 * c.size)) - 1
      if (v - c.prev) & mask ~= fh[6] & mask then c.ok = false end
    end
    c.prev = v
  end
  if n < F then return end
  local z = "none"
  if st.z80 then
    local f = io.open(Z80FILE, "rb")
    if f then
      local data = f:read("a")
      f:close()
      z = string.format("file:%s:%d", Z80FILE, #data)  -- sha1 computed by the host (Lua has no sha1)
    end
  end
  local fc = {}
  for _, c in pairs(cand) do  -- passing intervals not contained in a wider passing one
    local inner = false
    for _, o in pairs(cand) do
      if o ~= c and o.ok and o.size > c.size and o.addr <= c.addr and c.addr + c.size <= o.addr + o.size then inner = true end
    end
    if c.ok and not inner then fc[c.addr] = true end
  end
  local facts = {
    z80_sha1_after_upload = z,
    ssp_after_init = st.ssp and L.hex(st.ssp) or "none",
    frame_counter = st.hits[6] > 0 and set_str(fc) or "none",
    jcart_reads = set_str(st.jr),
    pad_reads = set_str(st.pr),
  }
  for k, h in pairs(IRQ) do
    facts["irq" .. k .. "_entry"] = st.hits[k] > 0 and L.hex(h.entry) or "none"
    facts["irq" .. k .. "_writes"] = st.lo[k] and (L.hex(st.lo[k]) .. "-" .. L.hex(st.hi[k])) or "none"
  end
  for key, value in pairs(facts) do L.emit{ev = "fact", key = key, value = value} end
  L.emit{ev = "stat", irq6_hits = st.hits[6], irq4_hits = st.hits[4], handler_writes = st.writes, stack_writes = st.stack}
  L.done{frames = n}
  manager.machine:exit()
end)
dbg:command("go")
