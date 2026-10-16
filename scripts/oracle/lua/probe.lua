-- 1.9 T2 RAM-series probe for scripts/oracle/probe.py: runs drive.lua (SCEN_LOAD, SCEN_INPUT, SCEN_POKES ...) and
-- appends the whole 68000 work RAM FF0000-FFFFFF (65,536 bytes) after every counted frame (after that frame's pokes)
-- to <ORACLE_OUT minus .jsonl>_ram.bin. Game-derived: the file stays under ignored .run/ and is never tracked.
-- Run: driven by PY scripts/oracle/probe.py (base and variant from one save state).
local LUADIR = os.getenv("ORACLE_LIB"):match("^(.*)/[^/]*$") or "."
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local P = os.getenv("ORACLE_OUT"):gsub("%.jsonl$", "")
local f = assert(io.open(P .. "_ram.bin", "wb"))

DRIVE_HOOK = function(n, L) f:write(sp:read_range(0xFF0000, 0xFFFFFF, 8)) end
DRIVE_DONE = function(n, L) f:close(); L.emit{ev = "ram", frames = n, bytes = 65536} end

assert(loadfile(LUADIR .. "/drive.lua", "t", _ENV))()  -- same env: drive.lua sees DRIVE_HOOK/DRIVE_DONE
