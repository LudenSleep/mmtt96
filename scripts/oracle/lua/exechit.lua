-- 1.9 T33 execution census: runs drive.lua (SCEN, SCEN_LOAD, SCEN_INPUT ...) with an exec breakpoint (lib.lua M.bp) on
-- every even address of the regions in env EXEC_REGIONS ("start-end ..." hex, end exclusive) plus one control address
-- that runs in every scenario: the level-6 interrupt target read from ROM vector 0x78 at start. The first hit of each
-- address is recorded with its counted frame, then that breakpoint is disabled (indices formatted hex, C0014).
-- Emits one {"ev":"exechit", frames, hits = ["ADDR@frame", ...], control, control_hits} before drive.lua's done.
-- Addresses and frames only; no ROM bytes. Run: SCEN=<id> EXEC_REGIONS=... PY scripts/oracle/mame.py run
--   scripts/oracle/lua/exechit.lua --frames <n> --tag t33x_<id> [--secs S]
local LUADIR = os.getenv("ORACLE_LIB"):match("^(.*)/[^/]*$") or "."
local L0 = dofile(os.getenv("ORACLE_LIB"))
local dbg = manager.machine.debugger
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local CONTROL = sp:read_u32(0x78) & 0xFFFFFF

local addrs = {CONTROL}
for a, b in (os.getenv("EXEC_REGIONS") or ""):gmatch("(%x+)%-(%x+)") do
  for x = tonumber(a, 16), tonumber(b, 16) - 1 do
    if x % 2 == 0 and x ~= CONTROL then addrs[#addrs + 1] = x end
  end
end
local index, first = {}, {}  -- addr -> bp index (from the console line "Breakpoint X set"), addr -> first frame
for _, a in ipairs(addrs) do
  local m = L0.mark()
  L0.bp(a)
  for i = m + 1, #dbg.consolelog do
    local k = tostring(dbg.consolelog[i]):match("Breakpoint (%x+) set")
    if k then index[a] = tonumber(k, 16) end
  end
end
local mark = L0.mark()

local function scan(n)
  for a in pairs(L0.bp_hits(mark)) do
    if not first[a] then
      first[a] = n
      if index[a] then dbg:command(string.format("bpdisable %X", index[a])) end
    end
  end
  mark = L0.mark()
end

DRIVE_HOOK = function(n, L) scan(n) end
DRIVE_DONE = function(n, L)
  scan(n)
  local hits, unset = {}, 0
  for _, a in ipairs(addrs) do
    if not index[a] then unset = unset + 1 end
    if a ~= CONTROL and first[a] then hits[#hits + 1] = string.format("%06X@%d", a, first[a]) end
  end
  table.sort(hits)
  L.emit{ev = "exechit", frames = n, hits = hits, control = L.hex(CONTROL), control_hits = first[CONTROL] or 0,
         bps = #addrs, bps_unset = unset}
end

assert(loadfile(LUADIR .. "/drive.lua", "t", _ENV))()  -- same env: drive.lua sees DRIVE_HOOK/DRIVE_DONE
