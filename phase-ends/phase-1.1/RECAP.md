MILESTONE: green

## Recap
Phase 1.1 built the first step of the decompilation: one command (`scripts/extract/manifest.py`) reads the game's ROM image, cuts it into labelled regions, and writes a manifest (a list of every region with its offset, size and fingerprint hash) to `config/manifest.retail.jsonl`. A second run produces a byte-identical manifest, and the repository's public audit now refuses to pass unless that manifest exists, because it uses the hashes to catch any game bytes that slip into git. The game's packed assets turned out to use Amiga Imploder compression (files marked "IMP!"); the new decoder unpacks all 368 of the 368 packed blobs, and each result is checked against the packer's own checksum. The Z80 sound driver (the program for the console's second, sound processor) sits uncompressed at 0x01597A-0x016DE6, and the game's real start address is inferred to be 0x000200: the reset vector points at 0, whose first word is an illegal instruction that traps through vector 0x10 to 0x000200; this has not yet been confirmed in an emulator. The block 0x020000-0x0477BA is still unlabelled code and data and is left to phase 1.2's disassembler.

Milestone evidence (this session): the milestone command chain exited 0 (manifest written, 749 records, `--check` OK, no git diff, audit 0 offenders among 219 paths; `.run/logs/pe-milestone.log`); both T4 negative controls re-run and reproduced: a planted copy of a raw region fails the audit (exit 1) and a missing manifest fails it (exit 1), manifest restored with a clean diff (`.run/logs/pe-negctl.log`). `tools/phaseend_index.py verify` itself reported RED with exit 127 because it does not quote the interpreter path (`C:/Program Files/...`); that is a harness defect, not a milestone failure (see Harness notes).

Open item: the developer pushed main to origin; whether the no-ROM CI run passed is not confirmed.

## Decisions that still bind
- Compression format name is `imp` (Amiga Imploder, magic "IMP!"): contract, recorded in `docs/ops/ops-setup-decomp.md:21` and `scripts/extract/manifest.py` `DECODERS`.
- Decoded manifest rows stay `status: inferred` until the phase 1.2 emulator cross-check promotes them: contract, recorded in `docs/ops/ops-setup-decomp.md:21`.
- Next task needs: phase 1.2 confirms the inferred entry 0x000200 (vector 0x10 trap) in an emulator, segments 0x020000-0x0477BA, and promotes decoded rows from `inferred`.
- Next task needs: confirm the no-ROM CI result for the pushed main before relying on CI as a gate.

## Harness notes
- harness: `tools/phaseend_index.py verify` runs `PY` unquoted; with `C:/Program Files/Python311/python.exe` it fails exit 127 ("C:/Program: No such file"). The clause was run by hand with a quoted interpreter.
- harness: `tools/phaseend_index.py assemble 1.1` lists only T1-T3 under `## Tasks` (header says 4 done; plan and `tasks/INDEX.md` both carry T4); PhaseEnd left script-owned, not hand-edited.
- harness: `tools/audit_public.py` has no `--help`; it runs the full audit (T4).
- harness: `tools/commit_task.sh` no longer stages `HOW_WE_WORK.md` automatically; pass it explicitly (script comment, line 57).
- harness: the hand-back enforcer forces an expert to hand back early while its background coder is still running (T2, T3); worked around with a committed progress file.
- harness: `expert-fable` is not installed on this tier, so T2 (`effort: high`) ran on `expert-opus55`.
- harness: retriever-web cannot write its pending report file; the expert transcribes the inline answer (T2).

## Deviations
- H7: T1 changed `.gitignore` and `config/firewall.txt` and introduced the extractor without a `HOW_WE_WORK.md`/`docs/ops/` edit in the same task; T4 (the planned docs task) added the ops doc and card rows. Recorded, no gap remains.
- `phase-ends/DIGEST.md` not updated although the closing brief asked: its only line marks it "frozen at the PA3 migration; not maintained", and `phaseend_index.py archive` does not write it. The cumulative record is `TASK_INDEX.md`, `RESEARCH_INDEX.md` and `PhaseEnd_Phase1.1.md`.
