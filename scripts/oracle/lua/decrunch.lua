-- Decrunch probe (mode from env ORACLE_MODE, default "natural"; or "all").
-- natural: cold boot + attract; bp at the Imploder wrapper entry 0x035416 logs A0 (blob), A1 (dest), A7 and the
-- return address; bp at its rts 0x035448 saves the decoded buffer (A0 = dest, D1 = rawSize there) to a fixed file,
-- which frame_done renames to <ORACLE_TRACE>_callN.bin. A frame with more than one return keeps only the last
-- buffer (earlier calls are emitted with file = null). Emits {"ev":"call", n, frame, pc_entry, ret, src, dest, dest_in,
-- sp, size, file}; pc_entry = entry address, ret = caller return address, dest_in = A1 at entry, dest = A0 at rts. Hex fields are 6/8-digit strings.
-- all: forced decode of every blob listed in ORACLE_BLOBS (one hex start per line). The first natural call's rts is
-- diverted (pc = a `bra.s *` found in ROM, the spin); each frame with nothing pending stages the next blob in debugger
-- temp0 and sets temp1 = 1; a bp on the spin (condition temp1 == 1) sets a0 = temp0, a1 = FF0100, pc = 0x035416 at an
-- instruction boundary and logs IMPIN (the entry bp does not fire after a pc write); the wrapper re-enters with the natural caller's return address still on the stack (never
-- popped), and its rts bp saves the buffer and diverts to the spin again. Emits {"ev":"natural", src, size} for the
-- hijacked call and {"ev":"forced", n, frame, src, src_in, dest, ok, size, sp, file} per blob (ok = D0 at rts,
-- FFFFFFFF = success); a blob with no rts within 1200 frames emits {"ev":"error"} and ends the run.
-- Env: ORACLE_LIB, ORACLE_OUT, ORACLE_TRACE, ORACLE_FRAMES (default 1200), ORACLE_MODE, ORACLE_BLOBS. Writes {"ev":"done"} last.
if ORACLE_DECRUNCH_LOADED then return end
ORACLE_DECRUNCH_LOADED = true
local L = dofile(os.getenv("ORACLE_LIB"))
local PFX = os.getenv("ORACLE_TRACE")
local F = tonumber(os.getenv("ORACLE_FRAMES") or "1200")
local MODE = os.getenv("ORACLE_MODE") or "natural"
local ENTRY, RET = 0x035416, 0x035448
local SAVE = PFX .. "_ret.bin"
local dbg = manager.machine.debugger

local function a24(s) return tonumber(s, 16) & 0xFFFFFF end  -- 68000 address bus: RAM prints as FFFFxxxx

L.open()
if MODE == "all" then
  local DEST, STALL = 0xFF0100, 1200
  local starts = {}
  for line in io.lines(os.getenv("ORACLE_BLOBS")) do
    local s = line:match("^(%x+)")
    if s then starts[#starts + 1] = tonumber(s, 16) end
  end
  local space = manager.machine.devices[":maincpu"].spaces["program"]
  local spin
  for a = 0x000200, 0x0FFFFE, 2 do
    if space:read_u16(a) == 0x60FE then spin = a break end
  end
  if not spin then
    L.emit{ev = "error", msg = "no bra.s * in ROM"}
    L.done{frames = 0}
    manager.machine:exit()
    return
  end
  dbg:command("temp1=0")
  dbg:command(string.format('bpset %X,1,{printf "IMPIN %%X %%X %%X",a0,a1,sp ; go}', ENTRY))
  dbg:command(string.format('bpset %X,1,{printf "IMPOUT %%X %%X %%X",a0,d1,d0 ; save %s,a0,d1 ; pc=%X ; go}',
                            RET, SAVE, spin))
  dbg:command(string.format('bpset %X,temp1==1,{temp1=0 ; a0=temp0 ; a1=%X ; pc=%X ; '
                            .. 'printf "IMPIN %%X %%X %%X",a0,a1,sp ; go}', spin, DEST, ENTRY))
  os.remove(SAVE)
  local mark, n, idx, pending, since, hijacked, last_in = L.mark(), 0, 0, false, 0, false, nil
  local function finish(extra)
    extra.frames = n
    extra.calls = idx
    L.done(extra)
    manager.machine:exit()
  end
  emu.register_frame_done(function()
    n = n + 1
    local log = dbg.consolelog
    for i = mark + 1, #log do
      local s = tostring(log[i])
      local a0, a1, sp = s:match("IMPIN (%x+) (%x+) (%x+)")
      if a0 then last_in = {src = a24(a0), dest = a24(a1), sp = a24(sp)} end
      local d, sz, ok = s:match("IMPOUT (%x+) (%x+) (%x+)")
      if d then
        if not hijacked then
          hijacked = true
          L.emit{ev = "natural", frame = n, src = last_in and L.hex(last_in.src), size = tonumber(sz, 16)}
        elseif pending then
          pending = false
          local file = string.format("%s_blob%d.bin", PFX, idx)
          os.remove(file)
          if not os.rename(SAVE, file) then file = nil end
          L.emit{ev = "forced", n = idx, frame = n, src = L.hex(starts[idx]), src_in = last_in and L.hex(last_in.src),
                 dest = L.hex(a24(d)), sp = last_in and L.hex(last_in.sp), ok = ok, size = tonumber(sz, 16), file = file}
        end
        last_in = nil
      end
    end
    mark = #log
    if hijacked and not pending then
      if idx >= #starts then return finish{} end
      idx = idx + 1
      since = n
      pending = true
      dbg:command(string.format("temp0=%X", starts[idx]))
      dbg:command("temp1=1")
    elseif pending and n - since > STALL then
      L.emit{ev = "error", msg = string.format("blob %d (%06X): no rts in %d frames", idx, starts[idx], STALL)}
      return finish{}
    elseif n >= F then
      return finish{}
    end
  end)
  dbg:command("go")
  return
end
if MODE ~= "natural" then
  L.emit{ev = "error", msg = "unknown mode " .. MODE}
  L.done{frames = 0}
  manager.machine:exit()
  return
end
dbg:command(string.format('bpset %X,1,{printf "IMPIN %%X %%X %%X %%X",a0,a1,sp,d@sp ; go}', ENTRY))
dbg:command(string.format('bpset %X,1,{printf "IMPOUT %%X %%X",a0,d1 ; save %s,a0,d1 ; go}', RET, SAVE))
os.remove(SAVE)

local calls, open, mark, n = 0, {}, L.mark(), 0
emu.register_frame_done(function()
  n = n + 1
  local log = dbg.consolelog
  local outs = {}
  for i = mark + 1, #log do
    local s = tostring(log[i])
    local a0, a1, sp, ret = s:match("IMPIN (%x+) (%x+) (%x+) (%x+)")
    if a0 then
      open[#open + 1] = {src = a24(a0), dest = a24(a1), sp = a24(sp), ret = a24(ret)}
    end
    local d, sz = s:match("IMPOUT (%x+) (%x+)")
    if d then outs[#outs + 1] = {dest = a24(d), size = tonumber(sz, 16)} end
  end
  mark = #log
  for i, o in ipairs(outs) do
    local c = table.remove(open, 1) or {}  -- FIFO: the wrapper is not re-entrant
    calls = calls + 1
    local file = nil
    if i == #outs and o.size > 0 then
      file = string.format("%s_call%d.bin", PFX, calls)
      os.remove(file)
      if not os.rename(SAVE, file) then file = nil end
    end
    L.emit{ev = "call", n = calls, frame = n, pc_entry = L.hex(ENTRY), ret = c.ret and L.hex(c.ret),
           src = c.src and L.hex(c.src), dest = L.hex(o.dest), dest_in = c.dest and L.hex(c.dest), sp = c.sp and L.hex(c.sp),
           size = o.size, file = file}
  end
  if n >= F then
    L.done{frames = n, calls = calls}
    manager.machine:exit()
  end
end)
dbg:command("go")
