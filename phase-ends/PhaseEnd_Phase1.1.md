# PhaseEnd — Phase 1.1: Extraction and manifest (implements Gen 1.1)
Approved: 2026-10-11 | Closed: 2026-10-11 | Planner: claude-opus-5-5/medium | Tasks: 4 done, 0 superseded

## Milestone
Milestone: one command regenerates the ROM region manifest, a second run is identical, the audit reads it as a required hash source — verified by: `PY scripts/extract/manifest.py && PY scripts/extract/manifest.py --check && git diff --exit-code config/manifest.retail.jsonl && PY tools/audit_public.py` (all exit 0, with `config/manifest.retail.jsonl` and `config/medium.sha1` on `required:` lines of `config/firewall.txt`)
Verified: `PY scripts/extract/manifest.py && PY scripts/extract/manifest.py --check && git diff --exit-code config/manifest.retail.jsonl && PY tools/audit_public.py` → exit 0; decoded 368/368, 749 records, check OK, diff clean, audit 0 offenders among 217 paths (.run/logs/t4-verify.log)

## Tasks
- T1 — manifest skeleton and firewall promotion | Done: `scripts/extract/manifest.py` generates `config/manifest.retail.jsonl` (medium + vectors, header, unknown gap) under the partition invariant; firewall requires the manifest and `config/medium.sha1`. | commit: - | tasks/T1.md | logs/T1.md
- T2 — locate Z80 driver and compressed blobs | Done: the regions TSV and manifest now hold 2 z80 regions (boot stub, raw sound driver), 368 Imploder "IMP!" compressed blobs tiling 0x0477BA-0x0FFB1A, and 2 padding runs. Three research reports are indexed. | commit: - | tasks/T2.md | logs/T2.md
- T3 — compression decoders | Done: stdlib IMP! (Imploder) decoder; manifest generator decodes 368/368 `compressed` rows to extracted/retail/decoded/<id>.bin with `decoded` records (`status: inferred`), refusing any mismatch by region id. | commit: - | tasks/T3.md | logs/T3.md

## Decisions that still bind
- T2 — compression format name for decode_<fmt>.py is `imp` (Amiga Imploder, magic "IMP!").
- T3 — decoded rows stay `status: inferred` until the phase 1.2 emulator cross-check promotes them.
- Compression format name is `imp` (Amiga Imploder, magic "IMP!"): contract, recorded in `docs/ops/ops-setup-decomp.md:21` and `scripts/extract/manifest.py` `DECODERS`.
- Decoded manifest rows stay `status: inferred` until the phase 1.2 emulator cross-check promotes them: contract, recorded in `docs/ops/ops-setup-decomp.md:21`.
- Next task needs: phase 1.2 confirms the inferred entry 0x000200 (vector 0x10 trap) in an emulator, segments 0x020000-0x0477BA, and promotes decoded rows from `inferred`.
- Next task needs: confirm the no-ROM CI result for the pushed main before relying on CI as a gate.

## Rules proposed
- (none)

## Cookbook entries added
C0001 | Name probe scripts uniquely; never shadow a stdlib module | python,scratch,gotcha | 2026-10-11 | 1.1/T2 | T2 summary gotcha
C0002 | Locate Amiga-packed blobs in an MD ROM: magic, header bound, packer checksum | megadrive,compression,imploder,extraction | 2026-10-11 | 1.1/T2 | R1.1-003
C0003 | Resolve an ambiguous compression spec by variant grid, all-or-nothing | compression,decoder,verification | 2026-10-11 | 1.1/T3 | T3 summary gotcha

## Research
R1.1-001 | T2 | Web: Codemasters MD Micro Machines compression and Z80 driver (public sources) | compression,z80,codemasters,web | retriever-web | 2026-10-11 | 28 lines
R1.1-002 | T2 | Findings: MMTT96 entry point, Z80 driver upload, IMP! (Imploder) compressed blobs | compression,z80,imploder,entry-point,regions | expert-opus55 | 2026-10-11 | 34 lines
R1.1-003 | T2 | Web: Amiga Imploder IMP! format spec (temisu/ancient IMPDecompressor) | compression,imploder,format-spec,web | retriever-web | 2026-10-11 | 20 lines

## Audit
- seed: no expert runs for phase 1.1
- CLAUDE.md: 983 bytes
- .claude/skills/project-architect/SKILL.md: 13113 bytes
- .claude-state/memory/MEMORY.md: 4262 bytes
- HOW_WE_WORK.md: 5592 bytes
- cookbook/INDEX.md: 727 bytes
- rules/INDEX.md: 7032 bytes
- audit unavailable: CLI not installed (~/.claude/pa3/pa_ledger.py)

## Agent runs
- (no ledger at ~\.claude\usage-ledger\ledger.sqlite)

## Discussions
- (none)

## Deferred
- from T4: phase 1.2 promotes decoded rows from `inferred`; the `unknown` 68000 region 0x020000-0x0477BA awaits the disassembler. (unconsumed)

## Changes
- 2026-10-11 router: T1 next -> done
- 2026-10-11 router: T2 next -> done
- 2026-10-11 router: T3 next -> done
- 2026-10-11 router: T4 next -> done

## Plain-English Recap
Phase 1.1 built the first step of the decompilation: one command (`scripts/extract/manifest.py`) reads the game's ROM image, cuts it into labelled regions, and writes a manifest (a list of every region with its offset, size and fingerprint hash) to `config/manifest.retail.jsonl`. A second run produces a byte-identical manifest, and the repository's public audit now refuses to pass unless that manifest exists, because it uses the hashes to catch any game bytes that slip into git. The game's packed assets turned out to use Amiga Imploder compression (files marked "IMP!"); the new decoder unpacks all 368 of the 368 packed blobs, and each result is checked against the packer's own checksum. The Z80 sound driver (the program for the console's second, sound processor) sits uncompressed at 0x01597A-0x016DE6, and the game's real start address is inferred to be 0x000200: the reset vector points at 0, whose first word is an illegal instruction that traps through vector 0x10 to 0x000200; this has not yet been confirmed in an emulator. The block 0x020000-0x0477BA is still unlabelled code and data and is left to phase 1.2's disassembler.

Milestone evidence (this session): the milestone command chain exited 0 (manifest written, 749 records, `--check` OK, no git diff, audit 0 offenders among 219 paths; `.run/logs/pe-milestone.log`); both T4 negative controls re-run and reproduced: a planted copy of a raw region fails the audit (exit 1) and a missing manifest fails it (exit 1), manifest restored with a clean diff (`.run/logs/pe-negctl.log`). `tools/phaseend_index.py verify` itself reported RED with exit 127 because it does not quote the interpreter path (`C:/Program Files/...`); that is a harness defect, not a milestone failure (see Harness notes).

Open item: the developer pushed main to origin; whether the no-ROM CI run passed is not confirmed.
