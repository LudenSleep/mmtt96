MILESTONE: green

## Recap
Phase 1.4 proved that real 68000 instruction source, not just raw data bytes, assembles back to the exact original game. An "assembler" is the program that turns text source into the binary; "instruction-form source" means readable machine instructions instead of `dc.b` byte lists; the "SHA-1" is a fingerprint of the whole ROM, so an equal SHA-1 means a byte-identical game. Phase 1.3's assembler, clownassembler, turned out unable to write one common instruction form the way the original does (a compare-with-a-constant written in its short original spelling, 1254 places in the game; report R1.4-002: it always rewrites that family into a different encoding), so the build now uses Macroassembler AS (the `asw` assembler plus the `p2bin` converter shipped in the same zip), fetched with the developer's prior approval: zip v1.4.2.20261012, 2,378,577 bytes, SHA-256 checked before extraction, the tools themselves ignored under `tools/bin/asl/` and only the fingerprint `tools/bin/asl.zip.sha256` tracked. A new command, `db.py listing`, turns any code region recorded in the Ghidra database (the reverse-engineering database) into instruction source under the ignored folder `asm/src/`, checks it in memory against the ROM, and the build uses that file in place of the region's data; all 194 verified code regions convert and match.

Milestone evidence (this session, 2026-10-12): with five regions (code_0139B0, code_01F800, code_010BA0, z80_upload_driver, vdp_dma) generated into `asm/src/` by `db.py listing` (each "match"), `tools/phaseend_index.py verify` ran the plan's chain `make clean && make build && make build SRC= && make build && audit_public && test -z "$(git ls-files asm build expected)"` and reported GREEN 1/1 (`.run/logs/pe14-verify2.log`, clause log `.run/logs/verify1.log`): `split: src 5 regions` then `build/mmtt96.bin: OK`, `split: src 0 regions` (the all-data `SRC=` build) then OK, five regions again then OK, `audit_public: OK` with 0 offenders among 348 paths, no tracked file under `asm`, `build` or `expected`. `asm/src/` was emptied afterwards. T4 also ran a fresh one-region switch and three negative controls (deliberate breakages): a perturbed operand fails with `end mismatch`, `SRC=` still builds OK, and deleting the source file re-splits and stays OK.

Facts established: T1 measured clownassembler's encoding choices with 64 armed size asserts; T3 classified every converter mismatch (classes A to E in `docs/encoding-map.md`) and fixed the converter for movem with (d16,PC), ori/andi to CCR/SR and (d8,PC,Xn); a zero displacement on an address register is written `0.w(An)`. The verdict is hand-written assembly: no link/unlk frames, no negative frame offsets, no stack cleanup after calls, no pea; the compiler kit phases 4 and 7 stay out unless contradicted. `split.py` includes `asm/src/<id>.asm` through the unchanged wrapper, `SRC=` forces all-data, `make clean` keeps `asm/src/`, and the Makefile now rebuilds when generated or source files change (the 1.3 gap P1.3-1 is closed). Stale clownassembler text was corrected and the CI comment at `no-rom.yml:19` fixed.

Open items: the developer reported pushing, but `origin/main` is still `08e1503`, with 74 local commits not on the remote before this close; the developer will re-push (agents never push).

## Decisions that still bind
- Build assembler is Macroassembler AS V1.42 Bld 313, `asw -q -xx -n -U -i .` then `p2bin`; clownassembler retired from the build: environment fact, card Environment Pins line, `docs/ops/ops-setup-decomp.md` pins row, `docs/encoding-map.md`.
- Listing source spells every size and the original mnemonic (cmp vs cmpi, add vs addi); zero (d16,An) is `0.w(An)`: contract, `db.py listing` self-check, `docs/encoding-map.md`.
- `make build SRC=` forces all-data; default `SRC=asm/src` includes any `asm/src/<id>.asm` present: contract, card Build line, ops doc, tested by the milestone chain.
- Instruction source and listings live only under ignored `asm/src/` and `.run/`; never in tracked files, logs or messages: contract, `tools/audit_public.py` disassembly-run cap, tested by the milestone chain.
- Hand-written verdict, no compiler kit phases 4 and 7 unless contradicted: scope, `docs/encoding-map.md`.
- Next task needs: P1.2-1 stays deferred to phase 1.5.
- Next task needs: the card names `docs/ops/INDEX.md` (Project, Pins, Docs map lines) but only `docs/ops/ops-setup-decomp.md` exists; create the index or repoint, within the 7000-char cap (card 6981).
- Next task needs: `asm/src/` is empty at close; regenerate regions with `db.py listing <id>` before an instruction-form build.

## Harness notes
- harness: router patch 27172b5 to `tools/phaseend_index.py`, first close with it. (1) `verify` quoted interpreter: worked, no exit 127. (2) clause splitter ignoring `;` inside parentheses: worked, the Milestone parsed as one clause. (3) `assemble` listing the closing task: worked, `## Tasks` lists T1-T4 with no manual edit. (4) discussion-index refresh keeping non-D triage rows: worked, `phase-ends/DISCUSSION_INDEX.md` still holds `P1.2-1 deferred:1.5` and `P1.3-1` after archive (P1.3-1 still reads `planned:1.4/T2`; its work was done in T2 and T4, status left as the tool wrote it). `archive` printed `RUN: ... gen-close 1.4` rather than running it; the closer ran gen-close once.
- harness: a fifth `verify` defect: an expected string with a placeholder (`split: src <n> regions`) was matched literally, so a passing chain reported RED 0/1 (`.run/logs/pe14-verify.log`); fixed at close (3 lines in `cmd_verify`: `<word>` placeholders match any non-blank run), re-run GREEN 1/1.
- harness: the hand-back enforcer forces early hand-backs while a background agent runs (every task and the planner); Agent `run_in_background:false` was ignored at least twice (T3, T4).
- harness: `task_log.py lint` rejects markdown tables in summaries, so a plan done-when asking for "a table" conflicts with it (T1).
- harness: a subagent's Write of `.run/probe/FINDINGS.md` was refused as "return findings as text"; coder findings went to `logs/T1.c1.md`.
- harness: expert-fable is not installed on this tier; T3 (plan `effort: high`) ran on expert-opus55.
- harness: `skill_add.py` collapsed `\\` in `--description` to `\` in both SKILL.md and the card line; fixed by hand at close.
- harness: GNU make (WinGet ezwinports) needs its `bin` on PATH in Git Bash (it was already on PATH for this close).
- harness: `tools/commit_task.sh` does not stage `HOW_WE_WORK.md`; passed explicitly.

## Deviations
- H7: every summary naming tools/build commands lists `HOW_WE_WORK.md` or `docs/ops/` (T1 ops doc; T2, T3, T4 card and ops doc); no miss.
- Docs (H23): the user-visible change (build assembler is AS, `asm/src/` + `SRC=`) is in README.md (T4 Files); no `CHANGES.md` in this project; no miss.
- Closer edited `tools/phaseend_index.py` (placeholder matching, above) and trimmed the dead card line `Harness gotchas that bite here: <!-- TODO ... -->` to fit the new skill line under the cap.
- Gotchas promoted: cookbook C0009 (encoding probe with per-case size asserts), C0010 (prove a source-include hook is live), C0011 (choose the assembler by a full-region scan); skill `edit-escapes-with-edit-tool`. No proposed rules were pending; none ratified.
