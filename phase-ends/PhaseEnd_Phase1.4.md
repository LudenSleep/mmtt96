# PhaseEnd — Phase 1.4: Assembler pinned (implements Gen 1.4)
Approved: 2026-10-12 | Closed: 2026-10-12 | Planner: claude-opus-5-5/medium | Tasks: 4 done, 0 superseded

## Milestone
Milestone: one assembler version and flags reproduce 3-5 probe routines byte-for-byte: `make build` with >= 3 verified `code` regions assembled from instruction-form source under ignored `asm/src/` emits a ROM whose SHA-1 equals the original; the same build with `SRC=` (all-data) also passes; the pinned assembler, its flags and `docs/encoding-map.md` are recorded — verified by: `make clean && make build && make build SRC= && make build && "C:/Program Files/Python311/python.exe" tools/audit_public.py && test -z "$(git ls-files asm build expected)"` (all exit 0; the instruction-form `make build` prints `split: src <n> regions` with n >= 3 and `build/mmtt96.bin: OK`)
Verified: make clean && make build && make build SRC= && make build && "C:/Program Files/Python311/python.exe" tools/audit_public.py && test -z "$(git ls-files asm build expected)" → exit 0 (.run/logs/t4_gate.log): src 5 regions OK, SRC= src 0 OK, src 5 OK, audit_public OK 0 offenders/346 paths, ls-files empty; asm/src emptied afterwards (0 files)

## Tasks
- T1 — clownassembler encoding probe | Done: every encoding trap class is measured on a synthetic asm68k probe under clownassembler v1.1.3 with 64 armed size asserts; defaults, forcing suffixes, switches and unsupported syntax are known; T3 flag set chosen. | commit: - | tasks/T1.md | logs/T1.md
- T2 — Ghidra listing export and split src hook | Done: `db.py listing <id>` writes asm68k source to asm/src/<id>.asm with self-check; split/Makefile include asm/src files via the unchanged wrapper, all-data with `SRC=`. | commit: - | tasks/T2.md | logs/T2.md
- T3 — game probes and encoding map | Done: build pinned to Macroassembler AS (asw+p2bin); 5 fully covered code regions build from instruction source with the ROM hash OK; docs/encoding-map.md records classes, flags, verdict. | commit: - | tasks/T3.md | logs/T3.md
- T4 — docs, CI comment, controls, milestone | Done: card, ops doc and README describe the AS build with ignored `asm/src/` + `SRC=`; negative controls measured; phase 1.4 milestone gate green from a clean tree with 5 source regions. | commit: - | tasks/T4.md | logs/T4.md

## Decisions that still bind
- T1 — T3 and later sources assemble with no switches from the source root; every short encoding is written explicitly (environment fact, recorded in docs/ops/ops-setup-decomp.md).
- T2 — listing output lives only under ignored paths (asm/src/, .run/); never in tracked files, logs or messages.
- T2 — `make build SRC=` forces all-data; default SRC=asm/src includes any asm/src/<id>.asm present.
- T3 — the build assembler is Macroassembler AS V1.42 Bld 313, `asw -q -xx -n -U -i .` then `p2bin`; clownassembler retired from the build (R1.4-002: it rewrites literal-source CMP/ADD/SUB/AND/OR to the I-form unconditionally, class A unreachable).
- T3 — verdict hand-written 68000 assembly; no compiler phases (kit phases 4 and 7 stay out) unless contradicted.
- T3 — listing source spells every size and the original mnemonic (cmp vs cmpi, add vs addi); zero (d16,An) is written `0.w(An)`.
- Build assembler is Macroassembler AS V1.42 Bld 313, `asw -q -xx -n -U -i .` then `p2bin`; clownassembler retired from the build: environment fact, card Environment Pins line, `docs/ops/ops-setup-decomp.md` pins row, `docs/encoding-map.md`.
- Listing source spells every size and the original mnemonic (cmp vs cmpi, add vs addi); zero (d16,An) is `0.w(An)`: contract, `db.py listing` self-check, `docs/encoding-map.md`.
- `make build SRC=` forces all-data; default `SRC=asm/src` includes any `asm/src/<id>.asm` present: contract, card Build line, ops doc, tested by the milestone chain.
- Instruction source and listings live only under ignored `asm/src/` and `.run/`; never in tracked files, logs or messages: contract, `tools/audit_public.py` disassembly-run cap, tested by the milestone chain.
- Hand-written verdict, no compiler kit phases 4 and 7 unless contradicted: scope, `docs/encoding-map.md`.
- Next task needs: P1.2-1 stays deferred to phase 1.5.
- Next task needs: the card names `docs/ops/INDEX.md` (Project, Pins, Docs map lines) but only `docs/ops/ops-setup-decomp.md` exists; create the index or repoint, within the 7000-char cap (card 6981).
- Next task needs: `asm/src/` is empty at close; regenerate regions with `db.py listing <id>` before an instruction-form build.

## Rules proposed
- (none)

## Cookbook entries added
C0009 | Probe assembler encodings with per-case size asserts per switch | assembler,probe,encoding,assert | 2026-10-12 | 1.4/T1 | T1 summary gotchas
C0010 | Prove a source-include hook is live: grep wrapper, not only hash | build,split,include,hash,gotcha | 2026-10-12 | 1.4/T2 | T2 summary gotchas
C0011 | Choose assembler by full-region scan: converter defect vs rewrite | assembler,listing,matching,ghidra | 2026-10-12 | 1.4/T3 | T3 summary gotchas

## Research
R1.4-001 | extract planner facts for assembler-pinned phase 1.4 | Phase 1.4 planning facts from 1.2/1.3 summaries | phase1.4, clownassembler, regions, ghidra, split.py, makefile | retriever-digest | 2026-10-12 | 28 lines
R1.4-002 | CMP/CMPI conversion in clownassembler and AS; movem label(pc) base; asm68k history | clownassembler vs AS: cmp #imm,Dn encoding and movem pc-rel base | clownassembler, asl, 68k, cmpi, b07c, movem | retriever-web | 2026-10-12 | 32 lines

## Audit
- seed: no expert runs for phase 1.4
- CLAUDE.md: 983 bytes
- .claude/skills/edit-escapes-with-edit-tool/SKILL.md: 725 bytes
- .claude/skills/project-architect/SKILL.md: 13113 bytes
- .claude/skills/run-sh-one-step/SKILL.md: 798 bytes
- .claude-state/memory/MEMORY.md: 4262 bytes
- HOW_WE_WORK.md: 7005 bytes
- cookbook/INDEX.md: 1945 bytes
- rules/INDEX.md: 7032 bytes
- audit unavailable: CLI not installed (~/.claude/pa3/pa_ledger.py)

## Agent runs
- (no ledger at ~\.claude\usage-ledger\ledger.sqlite)

## Discussions
- (none)

## Deferred
- from T4: phase 1.4 closed; build is AS; `db.py listing <id> --out asm/src` + `make build` is the source path; asm/src is empty at close. (unconsumed)

## Changes
- 2026-10-12 router: T1 next -> done
- 2026-10-12 router: T2 next -> done
- 2026-10-12 router: T3 next -> done
- 2026-10-12 router: T4 next -> done

## Plain-English Recap
Phase 1.4 proved that real 68000 instruction source, not just raw data bytes, assembles back to the exact original game. An "assembler" is the program that turns text source into the binary; "instruction-form source" means readable machine instructions instead of `dc.b` byte lists; the "SHA-1" is a fingerprint of the whole ROM, so an equal SHA-1 means a byte-identical game. Phase 1.3's assembler, clownassembler, turned out unable to write one common instruction form the way the original does (a compare-with-a-constant written in its short original spelling, 1254 places in the game; report R1.4-002: it always rewrites that family into a different encoding), so the build now uses Macroassembler AS (the `asw` assembler plus the `p2bin` converter shipped in the same zip), fetched with the developer's prior approval: zip v1.4.2.20261012, 2,378,577 bytes, SHA-256 checked before extraction, the tools themselves ignored under `tools/bin/asl/` and only the fingerprint `tools/bin/asl.zip.sha256` tracked. A new command, `db.py listing`, turns any code region recorded in the Ghidra database (the reverse-engineering database) into instruction source under the ignored folder `asm/src/`, checks it in memory against the ROM, and the build uses that file in place of the region's data; all 194 verified code regions convert and match.

Milestone evidence (this session, 2026-10-12): with five regions (code_0139B0, code_01F800, code_010BA0, z80_upload_driver, vdp_dma) generated into `asm/src/` by `db.py listing` (each "match"), `tools/phaseend_index.py verify` ran the plan's chain `make clean && make build && make build SRC= && make build && audit_public && test -z "$(git ls-files asm build expected)"` and reported GREEN 1/1 (`.run/logs/pe14-verify2.log`, clause log `.run/logs/verify1.log`): `split: src 5 regions` then `build/mmtt96.bin: OK`, `split: src 0 regions` (the all-data `SRC=` build) then OK, five regions again then OK, `audit_public: OK` with 0 offenders among 348 paths, no tracked file under `asm`, `build` or `expected`. `asm/src/` was emptied afterwards. T4 also ran a fresh one-region switch and three negative controls (deliberate breakages): a perturbed operand fails with `end mismatch`, `SRC=` still builds OK, and deleting the source file re-splits and stays OK.

Facts established: T1 measured clownassembler's encoding choices with 64 armed size asserts; T3 classified every converter mismatch (classes A to E in `docs/encoding-map.md`) and fixed the converter for movem with (d16,PC), ori/andi to CCR/SR and (d8,PC,Xn); a zero displacement on an address register is written `0.w(An)`. The verdict is hand-written assembly: no link/unlk frames, no negative frame offsets, no stack cleanup after calls, no pea; the compiler kit phases 4 and 7 stay out unless contradicted. `split.py` includes `asm/src/<id>.asm` through the unchanged wrapper, `SRC=` forces all-data, `make clean` keeps `asm/src/`, and the Makefile now rebuilds when generated or source files change (the 1.3 gap P1.3-1 is closed). Stale clownassembler text was corrected and the CI comment at `no-rom.yml:19` fixed.

Open items: the developer reported pushing, but `origin/main` is still `08e1503`, with 74 local commits not on the remote before this close; the developer will re-push (agents never push).
