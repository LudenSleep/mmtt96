# PhaseEnd — Phase 1.2: Oracles and load map (implements Gen 1.2)
Approved: 2026-10-11 | Closed: 2026-10-12 | Planner: claude-opus-5-5/medium | Tasks: 5 done, 0 superseded

## Milestone
Milestone: the Ghidra database rebuilds from the tracked text export and re-exports identically; a headless MAME oracle is scripted; every ROM/RAM/IO map claim carries >= 3 consistent live datapoints; the entry point and all 368 decoded rows are `verified` — verified by: `PY scripts/ghidra/db.py roundtrip && PY scripts/oracle/check_maps.py --live && PY scripts/extract/manifest.py && PY scripts/extract/manifest.py --check && git diff --exit-code config/manifest.retail.jsonl && PY scripts/oracle/check_maps.py --manifest && PY tools/audit_public.py` (all exit 0; `--manifest` asserts 0 `inferred` decoded rows and the entry row `verified`)
Verified: `PY scripts/ghidra/db.py roundtrip && PY scripts/oracle/check_maps.py --live && PY scripts/extract/manifest.py && PY scripts/extract/manifest.py --check && git diff --exit-code config/manifest.retail.jsonl && PY scripts/oracle/check_maps.py --manifest && PY tools/audit_public.py` → all exit 0 (roundtrip identical; --live OK 12 claims; manifest check OK; diff clean; --manifest OK 12 claims; audit 0 offenders)

## Tasks
- T1 — Ghidra headless db and text-export round trip | Done: `scripts/ghidra/db.py probe|rebuild|export|roundtrip` drives headless Ghidra 12.1.4; annotations live as text in `config/ghidra/*.tsv` and round-trip byte-identically through a fresh project. | commit: - | tasks/T1.md | logs/T1.md
- T2 — MAME headless oracle and entry-point proof | Done: MAME runs the dump headless as an oracle (`scripts/oracle/mame.py probe|run`); entry 0x000200 and z80_upload 0x015918 are verified claims in `config/maps/rom.tsv` with 3 runs, checked live by `check_maps.py`. | commit: - | tasks/T2.md | logs/T2.md
- T3 — decruncher harness, promote compressed and decoded rows | Done: decruncher 0x035416 driven inside MAME for all 368 blobs, 368/368 equal to offline decode; decoded manifest rows and compressed regions rows now `verified` (`emu:` evidence); natural decrunch buffer claimed in ram.tsv. | commit: - | tasks/T3.md | logs/T3.md
- T4 — segment 68000 code and data below 0x0477BA | Done: every former `unknown` gap row below 0x0477BA is now a `code_`/`data_` row (verified or inferred with reason), backed by 4 MAME PC-coverage runs and a seeded Ghidra analysis; manifest, roundtrip and audit green. | commit: - | tasks/T4.md | logs/T4.md

## Decisions that still bind
- T1 — annotations of record are `config/ghidra/*.tsv`; the Ghidra project under `ghidra/` is disposable, rebuilt by `db.py rebuild`.
- T1 — export holds only owned symbols (USER_DEFINED/IMPORTED, non-default names); auto-analysis output never exported.
- T2 — oracle is MAME 0.289, `megadriv microm96` (software list slot rom_mm96, J-Cart with EEPROM); no BizHawk fallback needed.
- T3 — decruncher convention 0x035416: in A0 = compressed blob, A1 = dest; out D1 = raw size, D0 = -1 (0xFFFFFFFF) ok / 0 fail; clobbers D0, A1, A5; rts at 0x035448.
- T3 — oracle files split: decrunch.tsv = forced harness (368 rows), decrunch_natural.tsv = natural in-game calls; check_maps decrunch_dest reads the natural file.
- T4 — rerun order for segmentation is coverage `--write` -> `classify.py seeds` -> `db.py analyse` -> `classify.py merge` -> manifest -> roundtrip.
- T4 — `verified` code = executed or Ghidra call/jump/flow-reachable from a verified unit (vectors alone do not verify); `verified` data = referenced only as data and never executed.
- T5 — a map claim with a `second` value must agree across MAME and BizHawk; disagreement = blocked with both outputs.
- T5 — MCP emulator bridge: none; revisit at phase 1.7 (ops doc).
- Annotations of record are `config/ghidra/*.tsv` (owned symbols only); `ghidra/` is disposable: contract, `docs/ops/ops-setup-decomp.md` oracles section, tested by `db.py roundtrip`.
- Region status rule (verified code = executed or reachable from verified code; verified data = data-referenced, never executed): contract, `docs/ops/ops-setup-decomp.md` classification lines, tested by `coverage.py --check`.
- Segmentation rerun order coverage `--write` -> `classify.py seeds` -> `db.py analyse` -> `classify.py merge` -> manifest -> roundtrip: environment fact, `docs/ops/ops-setup-decomp.md` and the card `ghidra_db` row.
- Decruncher 0x035416 convention and oracle file split (`decrunch.tsv` forced, `decrunch_natural.tsv` natural): contract, `docs/ops/ops-setup-decomp.md`, tested by `decrunch.py --all` and `check_maps.py`.
- A claim with a `second` column must agree across MAME and BizHawk; disagreement is `blocked` with both outputs: contract, `docs/ops/ops-setup-decomp.md`, tested by `check_maps.py --live`.
- MAME 0.289 `megadriv microm96` is the primary oracle; BizHawk 2.11 is second: environment fact, card Paths `Oracles:` line.
- MCP bridge: none; revisit at phase 1.7: scope, `docs/ops/ops-setup-decomp.md` MCP decision.
- Next task needs: phase 1.3 can rely on `config/maps/{rom,ram}.tsv` and `check_maps.py --live` (run detached via `run.sh --bg/--wait`; can exceed 285 s).
- Next task needs: 97 `inferred` partition rows (incl. 0x0419EE bad bytes, `pad_01facc`, 0x020000-0x035416 data) remain for later phases to confirm.

## Rules proposed
- (none)

## Cookbook entries added
C0004 | Headless Ghidra on Windows: paren args, stdin, markers, thunks | ghidra,headless,windows,gotcha | 2026-10-12 | 1.2/T1 | T1,T4 summary gotchas
C0005 | MAME debugger+Lua as a 68000 oracle: sp, pc+2, soft_reset, trace | mame,oracle,lua,68000,gotcha | 2026-10-12 | 1.2/T2 | T2,T3,T4 summary gotchas
C0006 | BizHawk Lua second oracle: reboot drops callbacks, firmware modal | bizhawk,oracle,lua,megadrive,gotcha | 2026-10-12 | 1.2/T5 | T5 summary gotchas

## Research
R1.2-001 | Ghidra/BizHawk/MAME headless + MCP capabilities for MD 68000 project | Mega Drive reassembly toolchain: Ghidra, BizHawk, MAME, MCP | ghidra, bizhawk, mame, mcp, jcart | retriever-web | 2026-10-11 | 35 lines

## Audit
- seed: no expert runs for phase 1.2
- CLAUDE.md: 983 bytes
- .claude/skills/project-architect/SKILL.md: 13113 bytes
- .claude/skills/run-sh-one-step/SKILL.md: 798 bytes
- .claude-state/memory/MEMORY.md: 4262 bytes
- HOW_WE_WORK.md: 6659 bytes
- cookbook/INDEX.md: 1185 bytes
- rules/INDEX.md: 7032 bytes
- audit unavailable: CLI not installed (~/.claude/pa3/pa_ledger.py)

## Agent runs
- (no ledger at ~\.claude\usage-ledger\ledger.sqlite)

## Discussions
- (none)

## Deferred
- from T5: phase 1.3 can rely on ram.tsv/rom.tsv claims and `check_maps.py --live` (MAME + BizHawk, run detached via run.sh --bg/--wait; > 285 s possible). (unconsumed)

## Changes
- 2026-10-11 router: T1 next -> done
- 2026-10-11 router: T2 next -> done
- 2026-10-12 router: T3 next -> done
- 2026-10-12 router: T4 next -> done
- 2026-10-12 router: T5 next -> done

## Plain-English Recap
Phase 1.2 gave the decompilation its two sources of truth, called oracles: a disassembler database that reads the game's code without running it, and emulators that run the game and let scripts watch its processor and memory. The database is Ghidra 12.1.4 run headless (no window); everything we add to it (names, comments, region types) is kept as plain text tables in `config/ghidra/`, and a rebuild from those tables re-exports them byte for byte. The main emulator is MAME 0.289, which runs the game's J-Cart dump as `megadriv microm96`; three runs confirmed the real start address: the reset vector points at address 0, whose first word is an illegal instruction, so the processor traps through vector 0x10 to 0x000200. Inside MAME we made the game's own unpacker (at 0x035416) unpack all 368 packed blobs, and every result matched our offline decoder (368 of 368), so all packed and unpacked rows are now marked verified. Four recorded play-throughs (10,014 distinct instruction addresses) plus Ghidra's analysis turned every unknown byte below 0x0477BA into a labelled code or data row, and the console's memory and I/O use was proven live, with BizHawk 2.11 as a second emulator agreeing with MAME.

Milestone evidence (this session, 2026-10-12): `db.py roundtrip` identical on 4 files (`.run/logs/m1-roundtrip.log`); `check_maps.py --live` OK 12 claims, MAME and BizHawk agreeing (`.run/logs/m2-live.log`); `manifest.py` 368/368 decoded, 1992 records, `--check` OK, `git diff --exit-code config/manifest.retail.jsonl` clean, `check_maps.py --manifest` OK, `audit_public.py` 0 offenders among 287 paths (`.run/logs/m3-chain.log`). Primary-artifact check: manifest has 368 decoded rows, 0 of them `inferred`; entry row r0002 0x000200 `verified` with 3 boot runs. `tools/phaseend_index.py verify` reported RED (exit 127, unquoted interpreter path) so the clauses were run by hand with a quoted interpreter (Harness notes).

Facts established: code rows 193 verified / 19 inferred, data rows 960 verified / 73 inferred (97 `inferred` partition rows in all, outside the milestone); 24 bytes near 0x0419EE flagged bad by Ghidra stay inferred; 0x020000-0x035416 is one large unreferenced data row; `pad_01facc` (1332 zero bytes) stays inferred because the bus-error vector points at it. RAM/IO: stack pointer after init 0xFFFFFC; vertical-blank handler 0x01F96A writes 0xFFC200-0xFFEE9B; no horizontal-blank handler runs; frame counter 0xFFC220; J-Cart reads 0x380001 and 0x38FFFE; joypad reads 0xA10003 and 0xA10005. Decruncher convention: A0 = packed blob, A1 = destination; returns D1 = size, D0 = -1 on success. No MCP bridge was adopted (revisit at phase 1.7).

Open items: the developer has set up Remote Control. Git holds 36 local commits not yet pushed (the developer pushes; agents never do).
