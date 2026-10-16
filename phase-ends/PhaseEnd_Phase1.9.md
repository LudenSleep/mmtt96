# PhaseEnd — Phase 1.9: Readability: the systems inventory, then every region readable (implements Gen 1.9)
Approved: 2026-10-13 | Closed: 2026-10-16 | Planner: claude-opus-5-5/medium | Tasks: 45 done, 2 superseded

## Milestone
Milestone: `docs/mechanics.md` explains every system of the inventory (sections in T4) in plain English, every claim line marked confirmed or hypothesis with resolving pointers and measured quantities where they exist, each system group signed off at developer review (T13 T15 T17 T19 T21 T23 T32 done); every code region of the ledger is readable (plate comment; every routine entry and nameable operand carries a meaning name with evidence or a neutral name with a recorded `unresolved:` verdict); hardware-register immediates render from generated `hw.inc`, game constants symbolic where proven; commentcheck 0 failed; build byte-identical from clean; health and the contract run green; CI green on the pushed history (developer's word, T37); card <= 7000 — verified by: `make clean && make build && make health && "C:/Program Files/Python311/python.exe" scripts/census/ledger.py check --complete && "C:/Program Files/Python311/python.exe" scripts/census/commentcheck.py && "C:/Program Files/Python311/python.exe" scripts/census/commentcheck.py --doc docs/mechanics.md && "C:/Program Files/Python311/python.exe" scripts/census/constants.py check && bash scripts/contract.sh --dump "disks/Micro Machines Turbo Tournament 96 (Europe) (v1.1) (J-Cart).md" && "C:/Program Files/Python311/python.exe" tools/audit_public.py && "C:/Program Files/Python311/python.exe" tools/card.py check && test -z "$(git ls-files asm build expected disks ghidra)"` (all exit 0; `build/mmtt96.bin: OK`, `health: pairs n/n agree`, `contract: OK`; long steps detached via `bash tools/run.sh --bg gate -- ...` + `--wait gate --max 280`, exit from `.run/logs/gate.exit`)
Verified: bash scripts/census/wave_gate.sh → wave_gate: OK (.run/logs/t45_gate.log)

## Tasks
- T1 — probe kit: scenarios and save states | Done: `drive.lua` drives 7 scenarios (h2h, racefull, playoff, pool, normal, kit, multi + J-Cart pair) by scripted pad inputs, each seen in a `.run/` snapshot, with ram_FFE69A sequences and race-start states `h2h_r1`, `challenge_r1`, `playoff_r1`, `pool_r1`, `normal_r1`, `multi_r1`; inventory in docs/ops/ops-tools.md "scenarios". | commit: - | tasks/T1.md | logs/T1.md
- T2 — probe kit: writer, VDP and poke probes | Done: `writers.lua` lists per-frame writers of WATCH RAM words, VDP registers and VDP access commands (+ slottab/pairrec series); `probe.py` diffs base vs variant RAM series from one state; `writers.tsv` (3 boot runs) and `probes.tsv` (P001-P006); self-test 4/4. | commit: - | tasks/T2.md | logs/T2.md
- T3 — hardware constants, game-constant sidecar, include split | Done: every immediate the game stores or bit-tests at a VDP control / Z80 bus / I/O port (100) renders over `config/names/hw.tsv` (100/100 symbolic, byte-identical); `consts.tsv` renders game constants (empty); `hw.inc`/`ram.inc`/`rom.inc` replace `names.inc`; health rung `constants` with a planted-value control. | commit: 9a84340 | tasks/T3.md | logs/T3.md
- T4 — doc checker, mechanics skeleton, wave gate, completeness check | Done: `commentcheck.py --doc` checks mechanics-doc claim lines (markers, pointers, confirmed strength); `docs/mechanics.md` skeleton (glossary, 7 groups, 33 sections, leads) passes it; `wave_gate.sh` chains the wave gate; `ledger.py check --complete` measures readability completeness. | commit: 61cd4af | tasks/T4.md | logs/T4.md
- T5 — locate view, scrolling and pool-table scale | Done: docs/mechanics.md sections View and scrolling and Pool-table levels answered by controlled probes P007-P021: no separate view object (scroll derived from cars each frame); view = bounding-box midpoint of the view set, 16 px/frame; Pool Slalom = half-scale engine mode set per course by a data byte plus half-size art. | commit: - | tasks/T5.md | logs/T5.md
- T6 — locate rules: scoring, out-of-view, playoff, race flow, difficulty | Done: docs/mechanics.md sections Scoring and win condition, Out-of-view scoring, Tie-break playoff, Race start and finish, Difficulty answered by controlled probes P022-P047 (h2h_r1, challenge_r1) and writer runs t6w_*: out of view = player 1's car vs the view (margins -20/300 x, -20/200 y stage px); point to the car further along the course; 8 lights, win at 8 or on lights when laps run out; 4-4 -> "Play Off!", next point decides; difficulty = per-race CPU data. | commit: - | tasks/T6.md | logs/T6.md
- T7 — locate course: boundary, out-of-bounds, laps, ramps, pickups | Done: docs/mechanics.md Group 3 filled: Track boundary and out-of-bounds, Lap detection and checkpoints, Ramps and airborne, Pickups and hazards, each with measured tables, marked claims and a Located: line; probes P048-P061. | commit: - | tasks/T7.md | logs/T7.md
- T8 — locate collisions: cars, collision areas, bounce, walls | Done: docs/mechanics.md Group 4 filled: Car-to-car collisions, Collision areas, Bounce and impulse response, with measured contact distances, a car-contact table and a wall table, marked claims and Located: lines; probes P062-P073. | commit: - | tasks/T8.md | logs/T8.md
- T9 — locate vehicle handling, AI and input incl. J-Cart | Done: docs/mechanics.md Group 5 filled (Acceleration, Top speed, Braking, Steering, Drift and traction, Vehicle types, Opponent AI, Input and J-Cart) with measured tables and Located: lines; probes P074-P100; two port names renamed. | commit: - | tasks/T9.md | logs/T9.md
- T10 — locate data: level storage, loading, construction kit, tables | Done: docs/mechanics.md Group 6 filled (Level data and loading with pool compare and capacity, Construction kit and saved tracks, Vehicle and track tables, Sound cues), each with Located: lines; probes P101-P108; writer runs t10w_*. | commit: - | tasks/T10.md | logs/T10.md
- T11 — system map and wave queue | Done: every code row of `config/campaign/ledger.tsv` has a `system` and `system_basis`; `config/campaign/batches.tsv` holds 28 whole-region batches in wave order; `ledger.py check` fails on an empty system or an unbatched row; `report` prints systems and batches. | commit: eded3f8 | tasks/T11.md | logs/T11.md
- T12 — wave: view and scrolling | Done: batches B001 and B002 (system view-and-scrolling, 10 regions, 1799 insns) have gone through procedure W: 13 RAM and 6 routine meaning names, 263 comments, 12 doc bullets, `unresolved:` verdicts on every other touched row; wave gate green. | commit: dac45be | tasks/T12.md | logs/T12.md
- T13 — close view and scrolling, developer review | Done: procedure G for View and scrolling and Pool-table levels: both sections complete, plain English, every open point with what settles it; REVIEW.md presents names, evidence, unchecked claims and the Mini Micro plan; wave gate green. | commit: - | tasks/T13.md | logs/T13.md
- T14 — wave: rules | Done: procedure W ran on the rules batches B003 (5 regions, 1213 insns) and B004 (2 regions, 1567 insns); both `done` in batches.tsv; wave_gate green. | commit: - | tasks/T14.md | logs/T14.md
- T15 — close rules, developer review | Done: procedure G for Out-of-view scoring, Tie-break playoff, Race start and finish, Difficulty: plain-English paragraph, open questions with settling runs, measured timeline; REVIEW.md with names, evidence, unchecked claims, banner quirk, FFD2BA reading; wave gate green. | commit: - | tasks/T15.md | logs/T15.md
- T16 — wave: course | Done: procedure W run twice for the course system: B005 (code_013BD6) and B006 (8 regions) are `done` in config/campaign/batches.tsv; 221 comments, 5 meaning names, struct field slot.f24, ~380 unresolved verdicts. | commit: - | tasks/T16.md | logs/T16.md
- T17 — close course, developer review | Done: procedure G for Track boundary, Lap detection, Ramps and airborne, Pickups and hazards: plain-words paragraphs, open-question blocks (6, 6, 5, 5) with settling runs; REVIEW.md with names, what each is, evidence class, T16 routing items; wave gate green. | commit: - | tasks/T17.md | logs/T17.md
- T18.1 — wave: collisions + 1 overflow run | Done: B007 (collisions) and B014 (rules overflow) through procedure W: comments, 13 meaning names, verdicts, mechanics claims; both `done` in config/campaign/batches.tsv; R1-R7 shift one slot (R7 ends at B028). | commit: - | tasks/T18.1.md | logs/T18.1.md
- T19 — close collisions, developer review | Done: procedure G for Car-to-car collisions, Collision areas, Bounce and impulse response: plain-words paragraphs, open-question blocks (6, 3, 6) with settling runs; REVIEW.md with 13 names, what each is, evidence class, T18.1 findings routed; wave gate green. | commit: - | tasks/T19.md | logs/T19.md
- T20 — wave: vehicle handling | Done: procedure W for vehicle handling (incl. AI and input): B008 and B009 named and commented, both `done` in config/campaign/batches.tsv. | commit: - | tasks/T20.md | logs/T20.md
- T21 — close vehicle handling, developer review | Done: procedure G complete for Acceleration, Top speed, Braking, Steering, Drift and traction, Vehicle types, Opponent AI, Input and J-Cart (plain words, open questions, exact one-frame recipe); REVIEW.md written for developer sign-off. | commit: cb1085c | tasks/T21.md | logs/T21.md
- T22 — wave: data | Done: B010 (kit editor, circuit check, checkpoint lists) and B011 (kit race setup, piece art, race maps, eight-car loop, EEPROM save) done in batches.tsv; structs maps, kitcourse, savedcourse; mechanics Group 6 course overview. | commit: - | tasks/T22.md | logs/T22.md
- T23 — close data, developer review | Done: Group 6 (Level data and loading, Construction kit, Vehicle and track tables, Sound cues) closed by procedure G with P111-P113 results and open-question lists; REVIEW.md restates what a new Mini Micro level needs. | commit: - | tasks/T23.md | logs/T23.md
- T24 — small rows: comments-only batches | Done: B012 and B013 (comments-only, unattended, insns < 50) done: 124 region plate comments against the listing, `unresolved:` verdicts on 301 neutral names; wave_gate green. | commit: d9ffa36 | tasks/T24.md | logs/T24.md
- T25 — rest wave R1 | Done: Batches B015 (per-course hooks) and B016 (cell events, object touches, bounce, lap steps) commented and verdicted under procedure W; both marked done in batches.tsv. | commit: - | tasks/T25.md | logs/T25.md
- T26 — rest wave R2 | Done: B017 (code_00C998, league season / time trial) and B018 (code_010EE2, construction kit menus, editors, save/load, password) at FULL depth: plates + eol, verdicts on every T8-neutral name touched, mechanics.md claims; batches done. | commit: - | tasks/T26.md | logs/T26.md
- T27 — rest wave R3 | Done: batches B019 and B020 through procedure W: every T8-neutral row has an `unresolved:` or evidence verdict, comments and mechanics claims added; no renames. | commit: - | tasks/T27.md | logs/T27.md
- T28 — rest wave R4 | Done: B021 and B022 (menu flow, driver select, name entry, Knockout, game over, season end) through procedure W; both batches done in config/campaign/batches.tsv; no renames. | commit: - | tasks/T28.md | logs/T28.md
- T29 — rest wave R5 | Done: B023 (menus, attract, init, Imploder) and B024 (credits, sounds, bonus race, line-up, stats) commented by procedure W at full depth; both batches done, wave T29. | commit: - | tasks/T29.md | logs/T29.md
- T30 — rest wave R6 | Done: B025 (menus/driver select/name entry/text and screen loads) and B026 (course hooks 20,21,6,33,34,4,51 + kit race) commented to procedure W depth; both batches done in batches.tsv. | commit: - | tasks/T30.md | logs/T30.md
- T31 — rest wave R7 | Done: B027 and B028 (last rest batches) worked to procedure W: comments, unresolved verdicts, mechanics hypotheses; all 28 campaign batches now `done`. | commit: - | tasks/T31.md | logs/T31.md
- T32 — close the rest, developer review | Done: docs/mechanics.md Group 7 closed by procedure G (Menus, Sound driver and music, Attract mode, Effects); Sound cues corrected (ram_FFE682 is the engine sound); REVIEW.md with unresolved counts per system. | commit: - | tasks/T32.md | logs/T32.md
- T33 — follow-ups: promote rows, re-kind rows, route vocabulary | Done: the 5 promote + 18 re-kind rows re-checked against scenarios P119-P132: 0 executed, verdicts unchanged; ledger routes are one of 5 tokens, enforced by `ledger.py check`. | commit: - | tasks/T33.md | logs/T33.md
- T34 — residual pass to complete readability | Done: every code row readable: `ledger.py check --complete` exit 0 (complete 252/252, no-plate 0, entries pending 0/715, raw operands 0, neutral pending 0/2201); `constants.py check` exit 0 (hw 100/100). | commit: - | tasks/T34.md | logs/T34.md
- T35 — docs to the readable state | Done: `docs/mechanics.md` opens with a Contents list, a one-page Overview and a "Names to know" table; README, the 68k doc and the ops docs describe the readable state (probe kit, wave gate, constants, completeness) and point to mechanics. | commit: 41239da | tasks/T35.md | logs/T35.md
- T36 — milestone proof | Done: the phase 1.9 milestone chain runs green clause by clause through `tools/run.sh` (contract with `--dump`: `contract: OK`); `docs/verification.md` holds the dated 2026-10-16 contract record; `phaseend_index.py verify` GREEN 1/1. | commit: - | tasks/T36.md | logs/T36.md
- T37 — CI green on the pushed history | Done: review prepared; REVIEW.md gives the developer the push, the CI check, cleanup and retrospective items. Not done until pushed + CI green + developer's word. | commit: - | tasks/T37.md | logs/T37.md
- T38 — rules group open runs | Done: writer runs and controlled probes P133-P137 settle finish order (FFD2BA-C0), end timer FFD65C, playoff timer hold, point-pause 701 step and FFD750 time-trial flag; mechanics.md verdicts updated. | commit: 490a861 | tasks/T38.md | logs/T38.md
- T39 — pairs.py names: ignore eol comment text | Done: pairs.py names pair compares eol comment text raw (not de-named), so a symbol named in an eol comment of a sampled region no longer makes names disagree; make health 9/9. | commit: - | tasks/T39.md | logs/T39.md
- T40.1 — rename pass: course and collisions names | Done: course RAM words, checkpoint/pair/height routines and the facing/state struct fields carry evidence-backed names; ram_FFD662 and ram_FFD65C doc statements fixed; ram_coast_p3/p4 confirmed by probe. | commit: - | tasks/T40.1.md | logs/T40.1.md
- T41 — vehicle handling open runs | Done: controlled probes P138-P152 recorded for all six asked runs; docs/mechanics.md Acceleration, Braking, Steering, Vehicle types verdicts and open questions updated. | commit: - | tasks/T41.md | logs/T41.md
- T42 — rename pass: vehicle handling names | Done: 0x0420E0/0x042192 named cpu_drive_p3/cpu_drive_p4 on one shared sighash; pad table FFD756-75C named ram_pad1_player..ram_pad4_player; slot field tokens f00/f12/f48/f5A replaced by x/y/movedir/speed. | commit: - | tasks/T42.md | logs/T42.md
- T43 — who reaches courses 50, 53, 54 | Done: courses 50, 53, 54 (the three unlisted Mini Micro courses) are the eight-car game's course list, reached by menus Extra Options > Party Play > 8 Player Share; writer census of ram_FFD672 recorded in docs/mechanics.md. | commit: - | tasks/T43.md | logs/T43.md
- T44 — kit half-scale black squares and kit AI steering | Done: docs/mechanics.md Construction kit states why kit squares are black at half scale (backdrop through transparent plane A, plane B never written) and that kit races have no computer cars (nothing steers by ram_dir_map), with probes P156-P160. | commit: - | tasks/T44.md | logs/T44.md
- T45 — eight-car course select: where the course names come from | Done: docs/mechanics.md Level data and loading now traces the eight-car names to the shared name list dat_04548A (by course number) and states what a fourth entry or a new course name needs. | commit: - | tasks/T45.md | logs/T45.md

## Decisions that still bind
- T1 — probe runs use a per-run EEPROM copy from `.run/mame/nvram_seed`; a run never inherits another run's saves (docs/ops/ops-tools.md).
- T2 — probe scripts drive scenarios through drive.lua hooks, loading it with `loadfile(path, "t", _ENV)` (a `dofile` runs in a different env and the hooks are invisible).
- T2 — writers controls are always on: positive `ram_frame_counter` FFC220 every frame (from frame 10 in boot runs), negative ROM header 000100 never written; writers_agg refuses a failing run.
- T3 — a hardware constant enters `hw.tsv` only with `published-doc: <source>` evidence (basereg rows: `rom:` evidence, and constants.py checks the invariant); game constants go to `consts.tsv` only with >= 3 datapoints or a confirmed mechanics claim.
- T3 — the in-scope set is "an immediate stored or bit-tested at a HW_PORTS address, resolved through absolute operands or a tracked port base"; constants.py exits 1 on any raw member. The vdp data port, PSG (C00011), J-Cart and the Z80 RAM mailbox stay raw (data or game protocol, not hardware constants).
- T4 — a mechanics claim is one `- ` bullet ending `[confirmed: ptrs]`, `[hypothesis: ptrs]` or bare `[hypothesis]` (open, no lead); `confirmed` = >= 3 distinct run ids or one `controlled` probe; tables and prose are not claims.
- T5 — scale questions use the same-vehicle pair Pool Slalom (list index 16, Mini Micro) vs Ball Chase (index 40, Pro), Ferry Fiasco as normal reference.
- T6 — idle or poked runs from a saved state use an unlisted SCEN id (no inputs, no saves); named scenarios replay inputs and overwrite their state.
- T11 — the system map is regenerated only by `systems.py map` (needs `ledger.py write` listing + Ghidra refs); `ledger.py write` keeps `system`/`system_basis`; waves own `batches.tsv` `status` (map refuses to overwrite a non-open batch without `--force`).
- T11 — system names: `view-and-scrolling rules course collisions vehicle-handling data`, `rest:<family>` (menus sound-driver music-effects attract input initialisation decompression other); no `camera`.
- T12 — RAM meaning names carry the house `ram_` prefix (`ram_view_x`); routine meaning names stay unprefixed. Later waves follow it.
- T24 — never add a routines.tsv row whose label equals a region-id entry; describe such entries with plate comments.
- T33 — ledger route vocabulary is `unattended developer-review promote re-kind keep-inferred`; the condition for promote/re-kind lives in the blocker column (contract: ops-tools.md + `ledger.py check`).
- T34 — Ghidra label symbols are applied after auto-analysis (postScript), never before; pre-analysis labels make Ghidra create/rename functions after them (`SymbolManager.createCodeSymbol` -> `tryUpdatingDefaultFunction`).
- Terminology: names, comments, headings and ledger rows use the period terms screen, view, scroll and level/stage, never a modern engine term for the view: `docs/ops/ops-tools.md` systems line, the T11 system names.
- A mechanics claim is one `- ` bullet ending `[confirmed: ...]` or `[hypothesis...]`; confirmed means >= 3 distinct run ids or one controlled probe: contract `commentcheck.py --doc` and its fixtures, `docs/ops/ops-tools.md` (T4).
- Meaning names need >= 3 datapoints or a confirmed mechanics claim; otherwise a neutral name with an `unresolved:` verdict; RAM names carry `ram_`, routines are unprefixed: `docs/ops/ops-tools.md` evidence rule (T12).
- `hw.tsv` rows need `published-doc:` evidence; the in-scope set of hardware immediates is checked by `constants.py check` (exit 1 on a raw member): contract `constants.py`, `docs/ops/ops-tools.md ## constants` (T3).
- Ledger routes are `unattended developer-review promote re-kind keep-inferred`, enforced by `ledger.py check`; readability completeness by `ledger.py check --complete`: `docs/ops/ops-tools.md` (T33, T34).
- Ghidra label symbols are applied after auto-analysis (postScript `labels` pass): `docs/ops/ops-setup-decomp.md`, cookbook C0043 (T34).
- Probe runs use a per-run EEPROM copy; idle runs from a saved state use an unlisted scenario id; drive hooks load with `loadfile(path, "t", _ENV)`: `docs/ops/ops-tools.md` (T1, T2, T6).
- `scripts/contract.sh` needs `PY` exported to the Python 3.11 interpreter: environment fact, skill `make-path-detached` (this close).
- Next task needs: the Group 7 open questions that a run can answer (menus, sound driver, attract): `docs/mechanics.md` Group 7 open-question blocks (T32).
- Next task needs: decoding the Z80 sound driver's music and effect data, for music extraction; the driver code is commented but its data is not decoded.
- Next task needs: whether the kit's 4 Player and 4 Player Teams races field computer cars, and which tiles the half-scale kit drawer keeps (`docs/mechanics.md` Construction kit open questions, T44).
- Next task needs: an eight-car course select with a fourth entry needs the shared course-name list `dat_04548A` extended or relocated (no free space), plus the per-course tables in the capacity lines (T45).
- Next task needs: the two renames above, only if the developer wants them, as a task owning `config/names/ram.tsv` and the names mirror (T35); the card has 19 chars headroom (6981/7000).

## Rules proposed
- (none)

## Cookbook entries added
C0032 | MAME runs: per-run EEPROM copy, save-state machine time, EEPROM layout by diff | mame,oracle,eeprom,savestate,gotcha | 2026-10-16 | 1.9/T1,T10 | T1,T10 summary gotchas
C0033 | Scripted menu input on MAME: spacing, poke plus press, state overwrite | mame,oracle,input,savestate,scenario | 2026-10-16 | 1.9/T1,T5,T6 | T1,T5,T6 summary gotchas
C0034 | MAME Lua env: loadfile into _ENV, proxy env to wrap a probe, tap pitfalls | mame,lua,oracle,probe,gotcha | 2026-10-16 | 1.9/T2,T38,T10,T32 | T2,T38,T10,T32 summary gotchas
C0035 | Probe design: positive and negative controls, discriminating pokes | oracle,probe,verification,controls | 2026-10-16 | 1.9/T2,T5,T6 | T2,T5,T6 summary gotchas
C0036 | Per-frame RAM sampling lands mid game-frame: read through it with taps | mame,oracle,ram,timing,probe | 2026-10-16 | 1.9/T5,T6,T8,T9 | T5,T6,T8,T9 summary gotchas
C0037 | Measure from recorded RAM series: raw dumps and single-frame prediction | oracle,ram,measurement,model | 2026-10-16 | 1.9/T7,T9 | T7,T9 summary gotchas
C0038 | MAME debugger breakpoints from a Lua hook: load census and blob swap | mame,debugger,lua,decompression,probe | 2026-10-16 | 1.9/T10,T43 | T10,T43 summary gotchas
C0039 | 68000/Mega Drive immediates: signed print, boot-loaded base reg, DMA mirror | 68000,megadrive,vdp,ghidra,constants | 2026-10-16 | 1.9/T2,T3 | T2,T3 summary gotchas
C0040 | comments.tsv: sort by address, eol before plate, or roundtrip differs | ghidra,comments,roundtrip,gotcha | 2026-10-16 | 1.9/T12,T30,T31 | T12,T30,T31 summary gotchas
C0041 | Comments and claims the checkers read: plate start, RANGE form, run ids | comments,commentcheck,claims,gotcha | 2026-10-16 | 1.9/T12,T16,T40.1,T43,T44 | phase 1.9 summary gotchas
C0042 | signatures propagate refusals and region-id label names | naming,signatures,build,gotcha | 2026-10-16 | 1.9/T20,T22,T24,T34,T42 | phase 1.9 summary gotchas
C0043 | Ghidra: label at a default function entry renames it; apply labels post-analysis | ghidra,headless,labels,gotcha | 2026-10-16 | 1.9/T34 | T34 summary gotchas
C0044 | Call-graph system assignment: hub votes mislead; identity evidence first | callgraph,census,routing,systems | 2026-10-16 | 1.9/T11 | T11 summary gotcha
C0045 | Claim checker: classify pointers by shape, one planted-bad line per kind | verification,fixture,commentcheck,claims | 2026-10-16 | 1.9/T4 | T4 summary gotcha

## Research
R1.9-001 | MMTT96 Mega Drive: construction kit access, track list, H2H rules, TT modes, multiplayer, cheats | MMTT96 menus, rules, tracks (web) | micro-machines, mega-drive, menus, rules | retriever-web | 2026-10-13 | 34 lines
R1.9-002 | one sentence + confirmed/hypothesis line counts per ### section of docs/mechanics.md | mechanics.md per-section plain summaries and tag counts | mechanics, overview, counts | retriever-digest | 2026-10-16 | 20 lines

## Audit
- seed: no expert runs for phase 1.9
- CLAUDE.md: 983 bytes
- .claude/skills/background-coder-handback/SKILL.md: 863 bytes
- .claude/skills/coder-commit-regate/SKILL.md: 811 bytes
- .claude/skills/decrunch-parent-remap/SKILL.md: 953 bytes
- .claude/skills/detached-run-exit-file/SKILL.md: 648 bytes
- .claude/skills/edit-escapes-with-edit-tool/SKILL.md: 725 bytes
- .claude/skills/make-path-detached/SKILL.md: 1096 bytes
- .claude/skills/mame-probe-recipes/SKILL.md: 1128 bytes
- .claude/skills/names-edit-mirror/SKILL.md: 630 bytes
- .claude/skills/project-architect/SKILL.md: 13113 bytes
- .claude/skills/propagate-refusal-test/SKILL.md: 731 bytes
- .claude/skills/run-sh-one-step/SKILL.md: 798 bytes
- .claude-state/memory/MEMORY.md: 4262 bytes
- HOW_WE_WORK.md: 7013 bytes
- cookbook/INDEX.md: 7400 bytes
- rules/INDEX.md: 7032 bytes
- audit unavailable: CLI not installed (~/.claude/pa3/pa_ledger.py)

## Agent runs
- (no ledger at ~\.claude\usage-ledger\ledger.sqlite)

## Discussions
- I1 | mechanics.md fixes: line 79 "(160, 112)" vs measured +8/-152/-104 (gives 144, 96); line 115 Pool Slalom row confirmed on | dropped
- I2 | tooling: consts.tsv symbol renderer so game constants (view catch-up 16, offsets 152/104, edge margins 321/225) get name | planned:1.9/T33
- I3 | Re-review the ten accepted T15 names (ram_lights_p1, ram_match_winner, ram_start_countdown, ram_in_view_p1, ram_playoff_ | planned:1.9/T35
- I4 | T19 hold: developer does a second read of docs/mechanics.md lines ~726-735 and ~832-840 (prose claims) before T19 closes | dropped
- I5 | T18.1 static findings (hold in inbox, no task this phase): fn_040d5a search range, fn_000a8c dead code 0x000B46-0x000B84 | deferred:gen2
- I6 | T33: include P072 diagonal-wall sweep and P068 working-slot writer run if scenarios allow. | planned:1.9/T33
- I7 | PROCESS REVIEW at next close (developer request, usage is high): review the PA3 loop for efficiency and propose changes | planned:1.9/T25
- I8 | PROCESS REVIEW format (developer): for each suggested efficiency change give an estimated saving (tokens or share of usa | planned:1.9/T25
- I9 | Process lesson (T24): two agents ran the wave gate at the same time in one tree and corrupted asm/ and build/ (false 'ha | planned:1.9/T25
- I10 | Developer decision (efficiency): no scope cuts or cheaper models; sound, music, effects and menus keep full depth. Compl | planned:1.9/T36
- I11 | NOTE for T34: apply T32 rename candidates z80_A01E00->z80_cmd_ring, z80_A01F03->z80_cmd_index (writer P104, reader P118) | planned:phase-1.9/T34
- I12 | next-generation planner: Group 7 run-answerable open questions in docs/mechanics.md (Menus, Attract mode, Effects, Sound | deferred:gen-next
- I13 | Next task needs: decode the Z80 sound data format (data_020000-02FA85, scores vs samples) for music extraction | deferred:gen-next

## Deferred
- T18 | superseded — wave: collisions
- T40 | superseded — rename pass: course and collisions names
- from T45: adding a Mini Micro course with a new number means relocating dat_04548A (no free space) plus the per-course tables in the capacity lines. (unconsumed)
- I5 (deferred:gen2): T18.1 static findings (hold in inbox, no task this phase): fn_040d5a search range, fn_000a8c dead code 0x000B46-0x000B84
- I12 (deferred:gen-next): next-generation planner: Group 7 run-answerable open questions in docs/mechanics.md (Menus, Attract mode, Effects, Sound
- I13 (deferred:gen-next): Next task needs: decode the Z80 sound data format (data_020000-02FA85, scores vs samples) for music extraction

## Changes
- 2026-10-13 router: T1 next -> done
- 2026-10-13 developer: Developer note 2026-10-13: not every pool-table course is of the mini-micro type; Pool Slalom (course 17, the T1 pool scenario) is the mini-micro format (small cars on a pool table with the tighter, zoomed-out look). T5 and T10 must CLASSIFY each pool-table course (17 Pool Slalom, unlisted 41 Ball Chase, and any others found) as mini-micro or not by evidence (sprite and tile scale, cars per screen, track size in tiles, screenshots), not by the word pool; a same-vehicle pair of a mini-micro and a non-mini-micro pool course would be a clean control for the scale question. The developer's term mini-micro goes in the docs/mechanics.md glossary as a developer term, a hypothesis for smaller sprites and tighter level art until evidenced
- 2026-10-13 router: T2 next -> done
- 2026-10-13 router: T3 next -> done
- 2026-10-13 router: T4 next -> done
- 2026-10-13 router: T5 next -> done
- 2026-10-13 router: T6 next -> done
- 2026-10-13 router: T7 next -> done
- 2026-10-13 router: T8 next -> done
- 2026-10-13 router: T9 next -> done
- 2026-10-13 router: T10 next -> done
- 2026-10-14 router: T11 next -> done
- 2026-10-14 T11: T11: 28 batches (38528 insns) = 28 runs held; rules 3, course 4, data 6 overflow 7 -> R1-R4; collisions 1 leaves T18 a spare run; B028 (rest:other) excess -> T18.1
- 2026-10-14 critic: reopened T18 as T18.1 — wave: collisions + 1 overflow run
- 2026-10-14 router: T12 next -> done
- 2026-10-14 developer: T13 review: sections, 13 RAM and 6 routine view names accepted; slot.f00/f12 stay neutral until the vehicle-handling wave; game constants stay plain numbers; T23 adds Mini Micro probes: kit course 66 flag forced on, kit themes viewed, course numbers 50/53/54 loaded
- 2026-10-14 developer: T13 next -> done
- 2026-10-14 router: T14 next -> done
- 2026-10-14 developer: added T38 — rules group open runs
- 2026-10-14 developer: T15 next -> done
- 2026-10-14 developer: T15 review: four rules sections and 10 meaning names accepted; open oracle runs and a ram_point_pause probe run now as the new task after T15
- 2026-10-14 router: T16 next -> done
- 2026-10-14 developer: T35 also re-reviews the ten T15 meaning names so each is easy to identify (clearer names or a plain-English name key in mechanics.md)
- 2026-10-14 developer: added T39 — pairs.py names: ignore eol comment text
- 2026-10-14 developer: added T40 — rename pass: course and collisions names
- 2026-10-14 developer: T17 next -> done
- 2026-10-14 developer: T17 review: group 3 and five course names accepted; pairs.py names fix task runs before T18.1; rename pass task runs after T19; open course runs go to T33; eight-car and four-player questions wait for save states
- 2026-10-14 router: T39 queued -> next
- 2026-10-14 router: T39 next -> done
- 2026-10-14 router: T39 follow-up for T33: pairs.py names compares plate comment lines raw; fix or confirm none falls in a sampled region
- 2026-10-14 router: T18.1 next -> done
- 2026-10-14 router: T18.1 findings routed: rename-pass lines in tasks/T18.1.md go to T40; follow-ups (fn_040d5a overrun, fn_000a8c dead code, fn_01e256 slot-8 read, fn_040a18 caller) go to T33
- 2026-10-14 developer: reopened T40 as T40.1 — rename pass: course and collisions names
- 2026-10-14 developer: T19 review: collisions names accepted except ram_coast_p3/p4 (recheck in T40.1); group 4 open runs deferred, diagonal-wall sweep and working-slot writer run flagged for T33; T19 held open for the developer's second read of mechanics.md prose
- 2026-10-14 developer: T19 next -> done
- 2026-10-14 router: T40.1 next -> done
- 2026-10-14 router: T20 next -> done
- 2026-10-14 developer: added T41 — vehicle handling open runs
- 2026-10-14 developer: added T42 — rename pass: vehicle handling names
- 2026-10-14 developer: T21 next -> done
- 2026-10-14 developer: T21 review: group 5 closed; open runs routed to the vehicle handling runs task, names to the rename pass after T33; open questions 6-9 and cross-group leads routed to later waves and T33
- 2026-10-14 router: T22 next -> done
- 2026-10-14 router: T22 finding routed to T33: split the fn_001978 / race_main signature group so the kit race entry can be named; other cross-group findings are in tasks/T22.md
- 2026-10-14 developer: added T43 — who reaches courses 50, 53, 54
- 2026-10-14 developer: added T44 — kit half-scale black squares and kit AI steering
- 2026-10-14 developer: T23 next -> done
- 2026-10-14 developer: T23 review: group 6 accepted; probe tasks added for who reaches courses 50/53/54 and kit half-scale black squares / kit AI steering
- 2026-10-14 router: T43 queued -> next
- 2026-10-14 router: T43 next -> done
- 2026-10-14 router: added T45 — eight-car course select: where the course names come from
- 2026-10-14 router: T24 next -> done
- 2026-10-14 router: T25 next -> done
- 2026-10-14 router: T25 routed to T34 naming pass: name fn_01ea82, fn_01f4f0, fn_01f6b8 (confirmed claims P054/P051/P048)
- 2026-10-15 router: T26 next -> done
- 2026-10-15 router: T27 next -> done
- 2026-10-15 router: T28 next -> done
- 2026-10-15 router: T29 next -> done
- 2026-10-15 router: T29 routed: T32 review settles whether ram_FFE682 is the player car engine sound or the course tune (P104-style run with slot 0 leaving view); T34 takes rename candidates from logs/T29.c1.md and T29.c2.md
- 2026-10-15 router: T30 next -> done
- 2026-10-15 router: T31 next -> done
- 2026-10-15 router: T31 closed all batches B001-B028; ledger check --complete still exit 1 (161/252 rows complete, 41/703 entries pending, 270 raw operands, 67/2143 neutral names pending): T34 clears it using rename candidates in logs/tasks T14-T31
- 2026-10-16 developer: T32 next -> done
- 2026-10-16 router: T33 next -> done
- 2026-10-16 router: T34 next -> done
- 2026-10-16 router: T35 next -> done
- 2026-10-16 router: T36 next -> done
- 2026-10-16 developer: T37 next -> done
- 2026-10-16 router: T38 next -> done
- 2026-10-16 router: T41 next -> done
- 2026-10-16 router: T42 next -> done
- 2026-10-16 router: T44 next -> done
- 2026-10-16 router: T45 next -> done

## Plain-English Recap
Phase 1.9 made the rebuilt game readable and explained how it plays. Every one of the 252 code regions now carries a plain-English heading comment, every routine and memory variable it touches has either a name backed by evidence or a neutral placeholder name with a written note of what would settle it, and every hardware register setting (video, Z80 bus and controller ports) is shown by name instead of as a bare number. Alongside the code, `docs/mechanics.md` explains each game system (driving, collisions, laps, the view that follows the cars, out-of-view scoring, the tie-break playoff, the pool-table levels, the construction kit, menus, sound and the rest), with every statement marked either confirmed by at least three emulator runs or one controlled experiment, or still a hypothesis with the run that would settle it. The developer reviewed each group of systems as it closed, and the rebuilt ROM is still byte-identical to the original, re-proved from a fresh clone.

The developer re-reviewed the ten names of the rules group (from T15) and left two proposed renames for a later decision: `ram_playoff_timer` to `ram_playoff_banner_timer` and `ram_point_pause` to `ram_point_pause_count`. Nothing was renamed. A usage guard (`tools/usage_guard.py`, `docs/usage_guard.md`) was installed but is not turned on. After this close the developer wants a full process retrospective: usage per task, how often experts had to be restarted, how far the gates overlapped, and what the review agents contributed, with savings and risks set side by side.
