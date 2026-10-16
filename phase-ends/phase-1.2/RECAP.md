MILESTONE: green

## Recap
Phase 1.2 gave the decompilation its two sources of truth, called oracles: a disassembler database that reads the game's code without running it, and emulators that run the game and let scripts watch its processor and memory. The database is Ghidra 12.1.4 run headless (no window); everything we add to it (names, comments, region types) is kept as plain text tables in `config/ghidra/`, and a rebuild from those tables re-exports them byte for byte. The main emulator is MAME 0.289, which runs the game's J-Cart dump as `megadriv microm96`; three runs confirmed the real start address: the reset vector points at address 0, whose first word is an illegal instruction, so the processor traps through vector 0x10 to 0x000200. Inside MAME we made the game's own unpacker (at 0x035416) unpack all 368 packed blobs, and every result matched our offline decoder (368 of 368), so all packed and unpacked rows are now marked verified. Four recorded play-throughs (10,014 distinct instruction addresses) plus Ghidra's analysis turned every unknown byte below 0x0477BA into a labelled code or data row, and the console's memory and I/O use was proven live, with BizHawk 2.11 as a second emulator agreeing with MAME.

Milestone evidence (this session, 2026-10-12): `db.py roundtrip` identical on 4 files (`.run/logs/m1-roundtrip.log`); `check_maps.py --live` OK 12 claims, MAME and BizHawk agreeing (`.run/logs/m2-live.log`); `manifest.py` 368/368 decoded, 1992 records, `--check` OK, `git diff --exit-code config/manifest.retail.jsonl` clean, `check_maps.py --manifest` OK, `audit_public.py` 0 offenders among 287 paths (`.run/logs/m3-chain.log`). Primary-artifact check: manifest has 368 decoded rows, 0 of them `inferred`; entry row r0002 0x000200 `verified` with 3 boot runs. `tools/phaseend_index.py verify` reported RED (exit 127, unquoted interpreter path) so the clauses were run by hand with a quoted interpreter (Harness notes).

Facts established: code rows 193 verified / 19 inferred, data rows 960 verified / 73 inferred (97 `inferred` partition rows in all, outside the milestone); 24 bytes near 0x0419EE flagged bad by Ghidra stay inferred; 0x020000-0x035416 is one large unreferenced data row; `pad_01facc` (1332 zero bytes) stays inferred because the bus-error vector points at it. RAM/IO: stack pointer after init 0xFFFFFC; vertical-blank handler 0x01F96A writes 0xFFC200-0xFFEE9B; no horizontal-blank handler runs; frame counter 0xFFC220; J-Cart reads 0x380001 and 0x38FFFE; joypad reads 0xA10003 and 0xA10005. Decruncher convention: A0 = packed blob, A1 = destination; returns D1 = size, D0 = -1 on success. No MCP bridge was adopted (revisit at phase 1.7).

Open items: the developer has set up Remote Control. Git holds 36 local commits not yet pushed (the developer pushes; agents never do).

## Decisions that still bind
- Annotations of record are `config/ghidra/*.tsv` (owned symbols only); `ghidra/` is disposable: contract, `docs/ops/ops-setup-decomp.md` oracles section, tested by `db.py roundtrip`.
- Region status rule (verified code = executed or reachable from verified code; verified data = data-referenced, never executed): contract, `docs/ops/ops-setup-decomp.md` classification lines, tested by `coverage.py --check`.
- Segmentation rerun order coverage `--write` -> `classify.py seeds` -> `db.py analyse` -> `classify.py merge` -> manifest -> roundtrip: environment fact, `docs/ops/ops-setup-decomp.md` and the card `ghidra_db` row.
- Decruncher 0x035416 convention and oracle file split (`decrunch.tsv` forced, `decrunch_natural.tsv` natural): contract, `docs/ops/ops-setup-decomp.md`, tested by `decrunch.py --all` and `check_maps.py`.
- A claim with a `second` column must agree across MAME and BizHawk; disagreement is `blocked` with both outputs: contract, `docs/ops/ops-setup-decomp.md`, tested by `check_maps.py --live`.
- MAME 0.289 `megadriv microm96` is the primary oracle; BizHawk 2.11 is second: environment fact, card Paths `Oracles:` line.
- MCP bridge: none; revisit at phase 1.7: scope, `docs/ops/ops-setup-decomp.md` MCP decision.
- Next task needs: phase 1.3 can rely on `config/maps/{rom,ram}.tsv` and `check_maps.py --live` (run detached via `run.sh --bg/--wait`; can exceed 285 s).
- Next task needs: 97 `inferred` partition rows (incl. 0x0419EE bad bytes, `pad_01facc`, 0x020000-0x035416 data) remain for later phases to confirm.

## Harness notes
- harness: `tools/phaseend_index.py verify` runs `PY` unquoted; with `C:/Program Files/Python311/python.exe` it fails exit 127 ("C:/Program: No such file"), and its clause splitter also cuts the Milestone at the parenthetical note (clause 2 = prose). Unfixed since 1.1; clauses run by hand.
- harness: the expert hand-back enforcer forces an early hand-back while a background coder runs (every task T1-T5; each cost a handoff and respawn).
- harness: `expert-fable` is not installed on this tier, so T2 (`effort: high`) ran on `expert-opus55`.
- harness: `analyzeHeadless.bat` fails on arguments with parentheses; the ROM is imported from an ignored paren-free copy.
- harness: MAME parses `a7` as hex (use `sp`); `soft_reset()` re-runs the autoboot script; a bp `printf pc` shows the instruction address +2.
- harness: EmuHawk shows a modal missing-firmware box on every cart load; `bizhawk.py` auto-closes exactly that box.
- harness: MAME wrote `cfg/` and `nvram/` into the repo root; now gitignored.
- harness: `tools/phaseend_index.py assemble 1.2` lists only T1-T4 under `## Tasks` (header says 5 done); same defect as 1.1; PhaseEnd left script-owned.
- harness: `tools/commit_task.sh` does not stage `HOW_WE_WORK.md`; pass it explicitly.

## Deviations
- H7: T3 added `scripts/oracle/decrunch.py` and changed `manifest.py`/`check_maps.py` without a `HOW_WE_WORK.md`/`docs/ops/` edit; fixed at close (ops doc decruncher lines). T4's status rule and T1's owned-only export rule were also added to the ops doc at close.
- Gotchas promoted: cookbook C0004 (Ghidra headless), C0005 (MAME oracle), C0006 (BizHawk oracle); skill `run-sh-one-step` (workflow). No proposed rules were pending; none ratified.
