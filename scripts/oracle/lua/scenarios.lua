-- T6 input scenarios for MAME probes (schedules from the T4 scratch scen.sh): name -> {frames, inputs}.
-- inputs: list of {frame, ioport field name, hold frames}; applied by the probe once per frame.
-- Used by: scripts/oracle/lua/values.lua (selects by env VALUES_SCEN).
local function rep(t, frames, name, dur)
  for _, f in ipairs(frames) do t[#t + 1] = {f, name, dur} end
  return t
end

local challenge = rep({}, {1000, 1200, 1400, 1700, 2000, 2300, 2950}, "P1 Start", 5)
challenge[#challenge + 1] = {3060, "P1 B", 540}
challenge[#challenge + 1] = {3300, "P1 Left", 20}

local proleague = {{1000, "P1 Start", 5}}
rep(proleague, {1100, 1120, 1140, 1160, 1180, 1200, 1220}, "P1 Down", 5)
proleague[#proleague + 1] = {1300, "P1 Start", 5}
rep(proleague, {1600, 1900, 2200, 2500, 2800, 3100}, "P1 Start", 5)
proleague[#proleague + 1] = {3200, "P1 B", 400}

-- 1.9 T1 scenarios for scripts/oracle/lua/drive.lua (optional fields: load = state name, save = {{frame, name}},
-- snaps = {frames}, pokes = {{frame, addr, bytes, value}}); a `load` scenario needs its state made first (order below)
-- and `--secs 900` (the state restores machine time). Inventory: docs/ops/ops-tools.md "scenarios".
local function hold(t, f, names, dur)  -- the same press on several fields
  for _, n in ipairs(names) do t[#t + 1] = {f, n, dur} end
  return t
end
-- first menu (frame ~750): 1 Player / 2 / 3 / 4 Player / 4 Player Teams / Extra Options; Start at 1000 = 1 Player
-- game-type menu (wraps, 9 rows): Challenge, Head To Head, ..., TT Single Race (= one Up)
local tt = {{1000, "P1 Start", 5}, {1100, "P1 Up", 5}, {1300, "P1 Start", 5}}
rep(tt, {1600, 1900, 2200}, "P1 Start", 5)  -- driver, name prompt, name entry end -> course select ~2950
local function ttrace(rights, t0)  -- course select: `rights` x Right, Start, "3 Laps" Start, A+Start
  local t = {}
  for _, h in ipairs(tt) do t[#t + 1] = h end
  for i = 1, rights do t[#t + 1] = {2950 + 60 * i, "P1 Right", 4} end
  t[#t + 1] = {t0, "P1 Start", 5}; t[#t + 1] = {t0 + 300, "P1 Start", 5}
  t[#t + 1] = {t0 + 600, "P1 A", 8}; t[#t + 1] = {t0 + 602, "P1 Start", 5}
  return t
end
local h2h = {{1000, "P1 Start", 5}, {1100, "P1 Down", 5}}
rep(h2h, {1300, 1600, 1900, 2200, 2500, 2800}, "P1 Start", 5)
local racefull = rep({}, {1000, 1200, 1400, 1700, 2000, 2300, 2950}, "P1 Start", 5)
-- Extra Options (5 Down) -> Construction Kit (3 Down) -> New (3 Down) -> Course Storage (5 Down) -> Save -> slot 3;
-- then Course Storage -> Load Course -> prompt -> picker Right x2 (slot 3) -> Start
local kit = rep({}, {800, 850, 900, 950, 1000}, "P1 Down", 4)
kit[#kit + 1] = {1100, "P1 Start", 5}
rep(kit, {1300, 1350, 1400}, "P1 Down", 4); kit[#kit + 1] = {1500, "P1 Start", 5}
rep(kit, {1800, 1850, 1900}, "P1 Down", 4); kit[#kit + 1] = {2000, "P1 Start", 5}
rep(kit, {2400, 2450, 2500, 2550, 2600}, "P1 Down", 4); rep(kit, {2700, 3000}, "P1 Start", 5)
rep(kit, {3200, 3250}, "P1 Down", 4); kit[#kit + 1] = {3350, "P1 Start", 5}
rep(kit, {3800, 3850, 3900, 3950, 4000}, "P1 Down", 4); kit[#kit + 1] = {4100, "P1 Start", 5}
kit[#kit + 1] = {4400, "P1 Down", 4}; kit[#kit + 1] = {4500, "P1 Start", 5}
rep(kit, {4800, 4850}, "P1 Down", 4); kit[#kit + 1] = {4950, "P1 Start", 5}
rep(kit, {5200, 5300}, "P1 Right", 4); kit[#kit + 1] = {5450, "P1 Start", 5}
-- 4 Player (3 Down) -> Single Race; per player: driver Start, name prompt Up (No) + Start; all four pads pressed
local ALL = {"P1 Start", "P2 Start", "P3 Start", "P4 Start"}
local multi = rep({}, {800, 850, 900}, "P1 Down", 4)
rep(multi, {1000, 1300}, "P1 Start", 5)
for k = 0, 3 do
  local b = 1600 + 450 * k
  hold(multi, b, ALL, 5); hold(multi, b + 200, {"P1 Up", "P2 Up", "P3 Up", "P4 Up"}, 5); hold(multi, b + 260, ALL, 5)
end
hold(multi, 3500, ALL, 5); hold(multi, 3800, ALL, 5)
local multi34 = hold({}, 1, {"P3 B", "P4 B"}, 400)  -- J-Cart pads 3-4 accelerate; control: multictl

return {
  challenge = {frames = 3600, inputs = challenge},
  proleague = {frames = 3600, inputs = proleague},
  attract = {frames = 3300, inputs = {}},
  -- 1.9 T1 (drive.lua); run order: h2h before playoff, multi before multi34/multictl
  h2h = {frames = 3500, inputs = h2h, save = {{3100, "h2h_r1"}}, snaps = {2700, 3450}},
  racefull = {frames = 7100, inputs = racefull, save = {{3050, "challenge_r1"}}, snaps = {3400, 7050}},
  playoff = {frames = 300, inputs = {}, load = "h2h_r1", pokes = {{3, 0xFFD164, 2, 0}, {3, 0xFFD166, 2, 0}},
             save = {{60, "playoff_r1"}}, snaps = {50, 130, 290}},
  pool = {frames = 5000, inputs = ttrace(16, 4000), save = {{4800, "pool_r1"}}, snaps = {3990, 5000}},
  normal = {frames = 5800, inputs = ttrace(23, 4420), save = {{5250, "normal_r1"}}, snaps = {4410, 5800}},
  kit = {frames = 5600, inputs = kit, snaps = {3340, 5440, 5600}},
  multi = {frames = 4300, inputs = multi, save = {{4150, "multi_r1"}}, snaps = {3750, 4300}},
  multi34 = {frames = 400, inputs = multi34, load = "multi_r1", snaps = {400}},
  multictl = {frames = 400, inputs = {}, load = "multi_r1", snaps = {400}},
  -- T42 pad-table census (writers.lua, WATCH/SCEN_PEEK FFD756:8): load-only, idle
  padc_challenge = {frames = 200, inputs = {}, load = "challenge_r1", snaps = {1, 200}},
  padc_h2h = {frames = 200, inputs = {}, load = "h2h_r1", snaps = {1, 200}},
  padc_multi = {frames = 200, inputs = {}, load = "multi_r1", snaps = {1, 200}},
}
