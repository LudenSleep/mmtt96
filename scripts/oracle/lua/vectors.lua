-- Probe: read the 64 vector longs live from the main CPU program space after frame 1; writes done.
-- Env: ORACLE_LIB, ORACLE_OUT. Vectors are addresses (md-spec), compared by mame.py with rom.parse_vectors.
local L = dofile(os.getenv("ORACLE_LIB"))
L.open()
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local n = 0
emu.register_frame_done(function()
  n = n + 1
  if n == 1 then
    local v = {}
    for i = 0, 63 do v[#v + 1] = string.format("%08X", sp:read_u32(i * 4)) end
    L.emit{ev = "vectors", v = v}
    L.done{frames = n}
    manager.machine:exit()
  end
end)
