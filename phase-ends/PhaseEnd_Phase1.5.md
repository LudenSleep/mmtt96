# PhaseEnd — Phase 1.5: Census and differential harness (implements Gen 1.5)
Approved: 2026-10-12 | Closed: 2026-10-12 | Planner: claude-opus-5-5/medium | Tasks: 5 done, 0 superseded

## Milestone
Milestone: scanners assert coverage; a second disassembler (Capstone 5.0.9, M68K_000) agrees with Ghidra on instruction boundaries over every verified code region (0 phantoms, 0 truncations, 0 unexplained disagreements, planted control caught); `make health` runs >= 5 differential question pairs with 0 disagreements; the census and progress report derive every denominator from the build — verified by: `make clean && make build && make health && "C:/Program Files/Python311/python.exe" tools/audit_public.py && test -z "$(git ls-files asm build expected)"` (all exit 0; `make health` prints `health: pairs <n>/<n> agree` with n >= 5 and `boundaries: verified <k>/<k> phantoms 0 truncations 0 unexplained 0`, k = verified code rows of `config/regions.retail.tsv`; run detached via `bash tools/run.sh --bg gate -- ...` + `--wait gate --max 280` per call if it exceeds 285 s)
Verified: make clean && make build && make health && audit_public.py && test -z "$(git ls-files asm build expected)" → exit 0 (`.run/logs/gate.log`: hash OK, health 7/7 agree, audit OK)

## Tasks
- T1 — Capstone second oracle and boundary diff | Done: Capstone 5.0.9 is a second 68000 oracle; `scripts/oracle/boundaries.py` diffs Ghidra listing rows against a Capstone linear sweep per region; verified scope agrees fully. | commit: - | tasks/T1.md | logs/T1.md
- T2 — census and progress report | Done: `scripts/census/census.py` (fixture + ROM census: dup groups, structural families, reach x size, unique tail) and `scripts/census/progress.py` (rows/bytes by kind x status with denominators) exist and pass. | commit: - | tasks/T2.md | logs/T2.md
- T3 — health chain with differential pairs | Done: `make health` runs 7 differential pairs plus the asm_leak firewall rung, prints `health: pairs 7/7 agree`, exits 0 in about 50 s; `make health-live` (check_maps --live, MAME + BizHawk) green, 12 claims. | commit: - | tasks/T3.md | logs/T3.md
- T4 — census findings: big data row, inferred rows, 0x0419EE | Done: every inferred row (19 code, 76 data at planning) and data_020000 carries a verdict; 43 rows promoted or re-kinded, 12 boundary exceptions added; 0x0419EE explained as a Ghidra decode gap. | commit: - | tasks/T4.md | logs/T4.md
- T5 — docs, card, ops index, milestone | Done: ops docs indexed (`docs/ops/INDEX.md`, new `docs/ops/ops-tools.md`); card gains census/boundaries/health rows at 6931 chars; phase 1.5 milestone gate green from a clean tree. | commit: - | tasks/T5.md | logs/T5.md

## Decisions that still bind
- T1 — Capstone 5.0.9 installed with the developer's approval; wheel sha256 matched PyPI (pin in docs/ops/ops-setup-decomp.md).
- T3 — `make health` is the closer's regression gate: green iff `health: pairs n/n agree` and exit 0; results in `.run/mmtt96-health/pairs/`, report `.run/mmtt96-health/report.txt`, child logs `.run/mmtt96-health/logs/<pair>.log`.
- T4 — data_020000 stays one verified data row until 1.6 checks a split (only 0x020000-0x02FA85 read; 22928 trailing bytes never read).
- T5 — `make health` is part of every phase-close gate (recorded in card gate line and `docs/ops/INDEX.md`)
- Capstone 5.0.9 (`M68K_000`) is the second 68000 oracle; pin and wheel sha256 in `docs/ops/ops-setup-decomp.md`: environment fact, card Pins and `docs/ops/INDEX.md` (already recorded by T1/T5).
- `make health` is part of every phase-close gate: green iff `health: pairs n/n agree` and exit 0: contract, card gate line, `docs/ops/INDEX.md`, tested by this milestone (T3, T5).
- Regions Ghidra cannot decode are listed by id in `config/oracle/boundary_exceptions.tsv`; nothing instruction-level leaves `.run/`: contract, `boundaries.py`, `asm_leak` rung.
- Next task needs: data_020000 stays one verified data row until 1.6 checks a split (its trailing 22928 bytes are never read).
- Next task needs: 1.6 re-kinds the 16 dispatch-reached data rows (V10) to code after seeding Ghidra at the 47 dispatch entries and re-splitting.
- Next task needs: 1.6 fixes code_0186A0's start (2 bytes early; the one `db.py listing` self-check mismatch); code_01A968, code_03581C, code_01FA2E stay inferred until entry evidence exists.
- Next task needs: kept inferred: 4 code rows and 48 data rows (V9-V13); each needs the evidence named in T4's verdicts.
- Next task needs: the next planner reads `docs/ops/INDEX.md` first for tool detail and pins.

## Rules proposed
- (none)

## Cookbook entries added
C0012 | MAME read taps vanish after remap: reinstall per frame, positive control | mame,oracle,lua,coverage,gotcha | 2026-10-12 | 1.5/T4 | T4 summary gotchas
C0013 | Ghidra Bad Instruction on valid 68000 words: Capstone cross-check first | ghidra,capstone,oracle,boundaries,gotcha | 2026-10-12 | 1.5/T4 | T4 summary gotchas

## Research
R1.5-001 | pick second m68k disassembler independent of Ghidra SLEIGH; Z80 option | Second independent 68000 (and Z80) disassembler for MD ROM cross-check | m68k, capstone, rizin, vda68k, musashi, z80dis, disassembler | retriever-web | 2026-10-12 | 41 lines

## Audit
- seed: no expert runs for phase 1.5
- CLAUDE.md: 983 bytes
- .claude/skills/detached-run-exit-file/SKILL.md: 648 bytes
- .claude/skills/edit-escapes-with-edit-tool/SKILL.md: 725 bytes
- .claude/skills/project-architect/SKILL.md: 13113 bytes
- .claude/skills/run-sh-one-step/SKILL.md: 798 bytes
- .claude-state/memory/MEMORY.md: 4262 bytes
- HOW_WE_WORK.md: 6994 bytes
- cookbook/INDEX.md: 2269 bytes
- rules/INDEX.md: 7032 bytes
- audit unavailable: CLI not installed (~/.claude/pa3/pa_ledger.py)

## Agent runs
- (no ledger at ~\.claude\usage-ledger\ledger.sqlite)

## Discussions
- (none)

## Deferred
- from T5: phase close; next phase planner reads `docs/ops/INDEX.md` first for tool detail and pins (unconsumed)

## Changes
- 2026-10-12 router: T1 next -> done
- 2026-10-12 router: T2 next -> done
- 2026-10-12 router: T3 next -> done
- 2026-10-12 router: T4 next -> done
- 2026-10-12 router: T5 next -> done

## Plain-English Recap
Phase 1.5 built the safety net the rest of the decompilation will lean on: tools that check our map of the game against independent evidence, so later work cannot quietly break it. A "region" is one row of `config/regions.retail.tsv`, a slice of the ROM marked as code or data and as verified (backed by evidence) or inferred (a guess). A "disassembler" turns machine code into readable instructions; until now only one (Ghidra) decided where each instruction starts. T1 added a second, independent one, Capstone 5.0.9 (the only install of the phase, approved by the developer, its wheel's SHA-256 matched PyPI), set to the plain 68000 mode (`M68K_000`, which correctly refuses a 68020-only encoding), and `scripts/oracle/boundaries.py` compares the two over every verified code region: a "phantom" is an instruction start one tool sees and the other does not, a "truncation" is the same start with a different length. They agree everywhere (194/194 regions at T1, 217/217 after T4; 0 phantoms, 0 truncations, 0 unexplained); the only spelling difference was `dbf` versus `dbra` (443 sites, treated as the same), and a deliberately planted error in code_0002FA is caught (193/194, 2 phantoms, 1 truncation, exit 1).

T2 added a "census" (`scripts/census/census.py`) that counts the whole ROM from the build's own files instead of typed numbers: 58 groups of byte-identical regions, 4 families of structurally identical code (15 member regions), a unique tail of 1291 rows, and 32 rows of at least 4096 bytes that nothing refers to; its 8-case fixture passes and each deliberately wrong answer fails. `scripts/census/progress.py` reports how much is verified, with every denominator from the build. T3 added `make health`, a chain of 7 "differential pairs" (two independent ways to answer one question, which must agree): boundaries, instruction-source build vs all-data build, incremental vs clean build, census vs manifest, region table vs Ghidra mirror, executed code vs code rows, and the runtime claims check. Each pair has a planted failure that makes it fire, a stale result is cleared before each run, and a firewall rung (`asm_leak`) confirms no instruction listing is tracked (0 runs in 378 tracked files at T3, a planted fixture caught); `make health-live` re-checks 12 claims in the emulators in about 10 s.

T4 used the new tools on every inferred row; the developer accepted its verdicts V1-V13. The gap at region code_0419EE is a Ghidra 12.1.4 decoding flaw (it rejects 4 valid two-word instruction forms, Capstone decodes them, and MAME executed all 13 slots in 3 of 3 forced runs and none in the control), so 8 code rows and 8 former data rows became verified code with 12 recorded boundary exceptions. Two 67-entry dispatch tables read by verified, executed code promoted 6 code rows and 16 data rows; code_01F964 is the horizontal-blank interrupt handler (7501 hits per forced run); init_table, data_0002EA, data_0359DE and data_020000 (read by video DMA, never executed) became verified data. Final census: code 217 verified and 4 inferred (578 bytes), data 980 verified and 48 inferred (24385 bytes), of 1623 rows; the T4 coder brief's 209 was an arithmetic slip (194 + 23 = 217). T5 created `docs/ops/INDEX.md` and `docs/ops/ops-tools.md` and added census, boundaries and health rows to the card.

Milestone evidence (this session, 2026-10-12): `tools/phaseend_index.py verify` ran the plan's chain `make clean && make build && make health && audit_public && test -z "$(git ls-files asm build expected)"` detached and reported GREEN 1/1, exit 0 (`.run/logs/pe15verify.log`, clause log `.run/logs/verify1.log`): `build/mmtt96.bin: OK`, `asm_leak: 391 files scanned, 0 runs`, `health: pairs 7/7 agree` with `boundaries: verified 217/217 phantoms 0 truncations 0 unexplained 0` (217 = verified code rows of the region table, counted from the file), `audit_public: OK` with 0 offenders among 391 paths, no tracked file under `asm`, `build` or `expected`, `asm/src/` empty. Planted controls re-run by the closer: `boundaries.py --scope verified --plant code_0002FA` gives 216/217, 2 phantoms, 1 truncation, exit 1 (`.run/logs/pe15plant.log`); `pairs.py boundaries --plant` DISAGREE, exit 1 (`.run/logs/pe15hplant.log`).

Open items: the developer reported pushing earlier, but `origin/main` is still `08e1503`, with 101 local commits not on the remote before this close; the developer will re-push (agents never push).
