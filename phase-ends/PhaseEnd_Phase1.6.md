# PhaseEnd — Phase 1.6: Multipliers and encoding map (implements Gen 1.6)
Approved: 2026-10-12 | Closed: 2026-10-13 | Planner: claude-opus-5-5/medium | Tasks: 6 done, 0 superseded

## Milestone
Milestone: one named routine (or table) propagates by signature to all its repeats (>= 3 members), each member byte-gated and the name registered fail-closed; listings render named RAM/IO variables and at least one struct instead of raw absolute addresses and still re-assemble byte-identically; every assembler form used by the verified code regions is in `docs/encoding-map.md` with a probe or region id as evidence, asserted by a scanner — verified by: `make clean && make build && make health && "C:/Program Files/Python311/python.exe" tools/audit_public.py && test -z "$(git ls-files asm build expected)"` (all exit 0; `make health` prints `health: pairs <n>/<n> agree` with n >= 9 (the 7 of 1.5 plus `signatures` and `names`), `boundaries: verified <k>/<k> phantoms 0 truncations 0 unexplained 0` with k = verified code rows of `config/regions.retail.tsv` counted from the file, and the encoding rung `encmap: forms <m>/<m> mapped`; run detached via `bash tools/run.sh --bg gate -- ...` + `bash tools/run.sh --wait gate --max 280` per call, exit code from `.run/logs/gate.exit`)
Verified: make clean && make build && make health && PY tools/audit_public.py && test -z "$(git ls-files asm build expected)" → exit 0 (health: pairs 9/9 agree; encmap: forms 394/394 mapped; boundaries 246/246; audit_public OK)

## Tasks
- T1 — region fixes: V10 re-kind, code_0186A0, data_020000 tail | Done: 16 V10 rows re-kinded to verified code (re-split where code and data alternate), 64 dispatch entries seeded as functions, code_0186A0 starts 0x0186A2, data_020000 split at 0x02FA86; listing 246/246 match; build + health green. | commit: 7a7bc4d | tasks/T1.md | logs/T1.md
- T2 — routine signatures, groups and propagation registry | Done: `signatures.py` scans exact/normalised/sequence signatures over every verified code row, groups them, propagates a name across a group behind a byte gate, and `check`s the registry; health pair `signatures` makes `make health` 8 pairs. | commit: - | tasks/T2.md | logs/T2.md
- T3 — name layer in the build: names.inc, listing names, mirror | Done: names from `config/names/*.tsv` reach the build (`asm/names.inc`), the `db.py` listing (names on/off), symbols.tsv (mirror) and `make health` (pair `names`, 9 pairs). | commit: - | tasks/T3.md | logs/T3.md
- T4 — first labelled routine: propagation demo, RAM and struct names | Done: largest routine group fNe3633717db (7 members, region code_013BD6) named once via `signatures.py propagate` as slotpair_test; RAM tables ram_slottab/ram_pairrec and structs slot (5 fields) and pairrec (10 fields) named with bytes plus MAME oracle evidence and rendered in the listing; planted-member refusal recorded. | commit: - | tasks/T4.md | logs/T4.md
- T5 — encoding-form coverage scanner and map completion | Done: `scripts/census/encodings.py` classifies 38504 instructions across 246 verified code regions into 394 forms, all mapped in `docs/encoding-map.md` Coverage section; health rung `encmap: forms 394/394 mapped` fails health on a gap. | commit: - | tasks/T5.md | logs/T5.md
- T6 — docs, card, ops, milestone | Done: name layer, signatures and encodings scanner documented in docs/ops; card has one `names` Tools row at 6991 chars; milestone gate green from a clean tree (9/9 pairs, encmap 394/394, boundaries 246/246). | commit: - | tasks/T6.md | logs/T6.md

## Decisions that still bind
- T1 — the verified code denominator for T2-T5 is 246 rows (144596 bytes), per progress.py after commit 7a7bc4d.
- T2 — function body = entry .. next entry or region end, over verified code rows only; bytes before a region's first entry are unowned and counted; region bodies scanned separately.
- T2 — group id = `f|r` + `E|N|S` + 10 hex of the layer hash; defined for singletons too, so `check` recomputes uniformly.
- T2 — propagate gate (until T3 rendering) = layer hash recomputed from `--rom` + `db.py listing` self-check `match` + `make build SRC=.run/signatures/src` OK, per member; any failure refuses the whole group; registry untouched.
- T3 — abs.w operand becomes a name only if the sign-extended word address equals the name's address; abs.l only if the 32-bit value equals the address with a zero high byte; else raw hex (AS silently emits a longer form for an abs.w name that cannot be sign-extended, e.g. the VDP control port). Immediates stay raw.
- T3 — code-name asserts live at the end of main.asm, not in names.inc (inside names.inc each name would be compared to its own generating value).
- T3 — names.inc emits ram.tsv rows, structs.tsv fields and only kind=code rows of routines.tsv; split refuses reserved names (68000 mnemonics, e.g. rts) and duplicate names/addresses.
- T3 — after editing config/names run `db.py mirror` then `db.py roundtrip`; pair `names` fails (unmirrored > 0) until then.
- T5 — form name `<mn>[.<sz>]:<modes>` (mnemonic unaliased, conditions collapsed bcc/dbcc/scc, branches .s/.w); unknown operand kinds render `?<type>.<am>` so they surface as unmapped, never silent.
- T5 — map Coverage section is generated by `encodings.py --write-map`, never hand-edited; the check fails on absent and count-stale forms.
- T6 — card detail for census/names tools lives in docs/ops/ops-tools.md; the card keeps one row per tool family pointing there
- Verified code denominator after T1: 246 rows, 144596 bytes, from `progress.py`: contract, the boundaries rung counts it from the file each run.
- Signature layers, group ids, function body = entry to next entry or region end over verified code only, propagate refuses whole groups: contract, `docs/ops/ops-tools.md` signatures section, tested by the `signatures` pair (T2, T6).
- Name rendering only when the encoding is reproduced (abs.w sign-extension, abs.l zero high byte, immediates raw); code-name asserts at the end of `main.asm`; reserved/duplicate names refused: contract, `docs/ops/ops-tools.md` names section, tested by the `names` pair (T3, T6).
- After any `config/names` edit: `db.py mirror`, `db.py roundtrip`, `pairs.py names`: workflow, skill `names-edit-mirror`, `docs/ops/ops-tools.md`.
- `docs/encoding-map.md` Coverage section is generated by `encodings.py --write-map`, never hand-edited; unknown operand kinds surface as unmapped: contract, the `encmap` health rung (T5).
- Card detail for census/names tools lives in `docs/ops/ops-tools.md`; the card keeps one row per tool family: environment fact, already applied by T6.
- Next task needs: key `config/oracle/decrunch*.tsv` by start address (positional manifest ids shift on every row insert; T1 remapped them by hand, skill `decrunch-parent-remap` until fixed).
- Next task needs: trim the card further; it is at 6989 of 7000 chars after this close.
- Next task needs: the 6 inferred code rows (code_01FA2E, code_03581C and the 4 lone returns code_01A404, code_01B166, code_01B8D0, code_01B934) and 26 inferred other rows keep the blockers named in 1.5/T4 and 1.6/T1.
- Next task needs: a value-logging census (written values across scenarios) could upgrade the placeholder struct field names (`w00`, `f12`, ...) and RAM names to meaning names (cookbook C0017).

## Rules proposed
- (none)

## Cookbook entries added
C0014 | MAME breakpoint indices are hex: format with %X before bpdisable | mame,oracle,debugger,gotcha | 2026-10-13 | 1.6/T1 | T1 summary gotchas
C0015 | 68000 read tap hit on a row's first word is prefetch, not a read | mame,oracle,68000,prefetch,gotcha | 2026-10-13 | 1.6/T1 | T1 summary gotchas
C0016 | make skips rebuild on same-second edits: delete target before controls | make,build,negative-control,gotcha | 2026-10-13 | 1.6/T3 | T3 summary gotchas
C0017 | Write census proves a field is written, not its meaning: name neutrally | naming,oracle,ram,struct,evidence | 2026-10-13 | 1.6/T4 | T4 summary gotchas
C0018 | Struct field at +0 renders as bare base name; 0 uses is expected | naming,listing,struct,gotcha | 2026-10-13 | 1.6/T4 | T4 summary gotchas
C0019 | Project script named like a stdlib module: load by path via importlib | python,import,stdlib,gotcha | 2026-10-13 | 1.6/T5 | T5 summary gotchas
C0020 | Capstone m68k reports d8(An,Xn) with d8=0 as base-displacement mode | capstone,68000,encoding,gotcha | 2026-10-13 | 1.6/T5 | T5 summary gotchas

## Research
- (none)

## Audit
- seed: no expert runs for phase 1.6
- CLAUDE.md: 983 bytes
- .claude/skills/decrunch-parent-remap/SKILL.md: 850 bytes
- .claude/skills/detached-run-exit-file/SKILL.md: 648 bytes
- .claude/skills/edit-escapes-with-edit-tool/SKILL.md: 725 bytes
- .claude/skills/names-edit-mirror/SKILL.md: 630 bytes
- .claude/skills/project-architect/SKILL.md: 13113 bytes
- .claude/skills/propagate-refusal-test/SKILL.md: 731 bytes
- .claude/skills/run-sh-one-step/SKILL.md: 798 bytes
- .claude-state/memory/MEMORY.md: 4262 bytes
- HOW_WE_WORK.md: 7015 bytes
- cookbook/INDEX.md: 3335 bytes
- rules/INDEX.md: 7032 bytes
- audit unavailable: CLI not installed (~/.claude/pa3/pa_ledger.py)

## Agent runs
- (no ledger at ~\.claude\usage-ledger\ledger.sqlite)

## Discussions
- (none)

## Deferred
- from T6: phase 1.7 starts from 9 pairs + encmap rung; any new tool gets a docs/ops/ops-tools.md section, card stays <= 7000 chars. (unconsumed)

## Changes
- 2026-10-12 router: T1 next -> done
- 2026-10-12 router: T2 next -> done
- 2026-10-13 router: T3 next -> done
- 2026-10-13 router: T4 next -> done
- 2026-10-13 router: T5 next -> done
- 2026-10-13 router: T6 next -> done

## Plain-English Recap
Phase 1.6 turned the verified map of the game into something that can carry names: a routine named once now reaches every byte-identical or structurally identical copy of itself, listings show named memory variables and structures, and every way the assembler writes an instruction in the verified code is documented and checked. A "region" is one row of `config/regions.retail.tsv`, a slice of the ROM marked code or data and verified (backed by evidence) or inferred (a guess). T1 first fixed the regions the earlier phase left open: Ghidra was seeded at the 47 entries of two dispatch tables (tables of routine addresses the game jumps through), which re-kinded the 16 dispatch-reached data rows to code (13 by Capstone descent from those entries, 3 only through the jump table data_0359DE), moved code_0186A0's start 2 bytes later to 0x0186A2 (the listing self-check now matches 246/246), reached code_01A968 by closure with an 8-byte data head, and split data_020000 at 0x02FA86 (the tail was read 0 times in 3 emulator runs whose positive control fired, has 0 references and is 34% invalid as code, so it is inferred data). Verified code rows went from 217 to 246 (144596 bytes), the table from 1623 to 1650 rows, inferred rows from 97 to 32 (6 of them code); 4 lone-return inferred rows got recorded `ghidra-unreached` boundary exceptions, and 9 of the 29 new verified code rows were seen executing in breakpoint probes.

T2 added `scripts/census/signatures.py`, which fingerprints every routine three ways: "exact" (same bytes), "normalised" (same bytes once addresses are masked) and "sequence" (same instruction shape). Its scan finds 698 function bodies covering 137122 of the 144596 verified code bytes (7474 bytes in 42 regions sit before a region's first entry and are counted as unowned); its 5-case fixture passes and each deliberately wrong answer fails; `propagate` writes a name to every member of a group and refuses the whole group if any member fails its byte gate. T3 added the name layer: `config/names/ram.tsv` (13 evidence-backed RAM and I/O addresses), `structs.tsv`, and `asm/names.inc` generated into the ignored build tree; the listing shows a name only where the assembler reproduces the same encoding (an absolute short address is named only when its sign-extended value equals the name's address, because the assembler otherwise silently emits a longer form), names are mirrored into the Ghidra symbol table, and reserved or duplicate names are refused. The firewall (no game-derived listing in tracked files) was re-proved first.

T4, accepted by the developer at review, named the largest group: 7 identical routines (fn_015508 and 6 others in region code_013BD6, called from 28 sites in fn_0153B6, one per pair of 8 slots) became `slotpair_test`, with structures `slot` and `pairrec` whose fields carry neutral offset names because the evidence shows they are written, not what they mean; the group never ran in 3 emulator runs, so the name rests on the bytes and on an executed 4-slot twin, code_00635E. T5 added `scripts/census/encodings.py`, which classifies all 38504 instructions of the 246 verified code regions into 394 assembler forms, all listed with evidence in `docs/encoding-map.md`, and a health rung that fails on any unlisted form; T6 documented all of it. `make health` now runs 9 differential pairs (two independent ways to answer one question that must agree).

Milestone evidence (this session, 2026-10-13): `tools/phaseend_index.py verify` ran the plan's chain `make clean && make build && make health && audit_public && test -z "$(git ls-files asm build expected)"` detached and reported GREEN 1/1, exit 0 (`.run/logs/pe-verify.log`, clause log `.run/logs/verify1.log`, fresh build and health report timestamps): `build/mmtt96.bin: OK`, `health: pairs 9/9 agree` (boundaries, srcform, incremental, census, mirror, coverage, checkmaps, signatures with 7 registry rows 0 drift, names 9/9 on and off), `boundaries: verified 246/246 phantoms 0 truncations 0 unexplained 0` (246 = verified code rows counted from the region file by the closer), `encmap: forms 394/394 mapped`, `audit_public: OK` 0 offenders among 438 paths, no tracked file under `asm`, `build` or `expected`.

Open items: `origin/main` is still `875a802` (the 1.5 close); 37 local commits were not on the remote before this close. The developer will push (agents never push).
