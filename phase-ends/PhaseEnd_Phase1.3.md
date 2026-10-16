# PhaseEnd — Phase 1.3: All-data baseline (implements Gen 1.3)
Approved: 2026-10-12 | Closed: 2026-10-12 | Planner: claude-opus-5-5/medium | Tasks: 3 done, 0 superseded

## Milestone
Milestone: `make build` regenerates an all-data source from the developer's own dump, assembles it and emits a ROM whose SHA-1 equals the original (100% data); the per-binary contract `config/check.retail.sha` is tracked and `required:` in the firewall; an absent dump makes `make build` refuse with a clear message — verified by: `make clean && make build && make expected && cmp build/mmtt96.bin expected/mmtt96.bin && ! make build ROM=.run/absent.md && PY tools/audit_public.py` (all exit 0; `make build` itself runs the boundary check and `sha1sum -c config/check.retail.sha`; `! make build ROM=...` exits non-zero and prints the refusal)
Verified: make clean && make build && make expected && cmp build/mmtt96.bin expected/mmtt96.bin && ! make build ROM=.run/absent.md && "C:/Program Files/Python311/python.exe" tools/audit_public.py -> exit 0 (`build/mmtt96.bin: OK`, cmp equal, absent dump refused, audit OK 0 offenders among 312 paths; .run/logs/t3_verify.log)

## Tasks
- T1 — assembler install and probe | Done: clownassembler v1.1.3 installed in ignored `tools/bin/`, sha256 tracked and checked; flat-binary command line and fatal boundary-assert form probed (pass and fail) and pinned in the ops doc. | commit: - | tasks/T1.md | logs/T1.md
- T2 — splitter, Makefile, hash contract | Done: `make build` from a clean tree splits the ROM into `asm/` (all-data) and reassembles `build/mmtt96.bin`, SHA-1 equal to the original (`build/mmtt96.bin: OK`). | commit: - | tasks/T2.md | logs/T2.md
- T3 — negative controls, firewall promotion, docs, milestone | Done: Phase 1.3 milestone green from a clean tree; four negative controls measured; `config/check.*.sha` is `required:` in the firewall; card, ops doc and CI comment describe `make build`. | commit: d21d0bc, b380173 | tasks/T3.md | logs/T3.md

## Decisions that still bind
- T1 — assembler = clownassembler v1.1.3 `tools/bin/clownassembler_asm68k.exe`, sha256 `9d18134fa7172ba8f068056c8773b7c4d4d3b554880c444e37fce1f66658b269`, 131,072 B, AGPL-3.0-or-later (env fact → ops doc row, done).
- T1 — command line `tools/bin/clownassembler_asm68k.exe //p <src.asm>,<out.bin>`; `/p` = flat binary, no header, no padding past the last byte. From Git bash / GNU make write `//p` (or set `MSYS_NO_PATHCONV=1`); a bare `/p` is rewritten to a path and fails rc=1.
- T1 — boundary assert form (end exclusive, hex): `\tif\t* <> $XXXXXX` / `\tinform\t3,"<msg>"` / `\tendc` → assembly fails rc=1 and no output file is written.
- T2 — the build gate is `make build` ending in `sha1sum -c config/check.retail.sha`; any byte drift fails it.
- T3 — Test/gate = `make build`, green = `build/mmtt96.bin: OK` and exit 0; decisive = `make clean && make build`.
- Assembler pin clownassembler v1.1.3, sha256 `9d18134f…b269`, command `//p <src>,<out>`: environment fact, `docs/ops/ops-setup-decomp.md` Version pins row and card Environment Pins line.
- Boundary assert form `if * <> $END` / `inform 3,"msg"` / `endc` (rc=1, no output): contract, ops doc pins row, emitted by `split.py`, proven by T3 control 2.
- The gate is `make build` ending in `sha1sum -c config/check.retail.sha`, green = `build/mmtt96.bin: OK` and exit 0; decisive = `make clean && make build`: contract, card Build/Test lines and ops doc build section, tested by the milestone chain.
- `config/check.*.sha` is `required:` in `config/firewall.txt`: contract, tested by `tools/audit_public.py` (exit 1 when missing).
- Next task needs: make `build/mmtt96.bin` depend on the generated `asm/` files; today a hand-tampered `asm/` file is only rebuilt after deleting the bin or `make clean`.
- Next task needs: the stale comment at `.github/workflows/no-rom.yml:19` ("full-fleet compile-only run") still needs fixing.
- Next task needs: the card `HOW_WE_WORK.md` is exactly at its 7000-char cap; any addition needs a trim elsewhere.
- Next task needs: P1.2-1 stays deferred to phase 1.5.

## Rules proposed
- (none)

## Cookbook entries added
C0007 | Native Windows /x switches from Git bash/make: MSYS path rewrite | windows,msys,make,assembler,gotcha | 2026-10-12 | 1.3/T1 | T1 summary gotchas
C0008 | Prove a boundary assert fires: taken branch, short region file | assembler,assert,build,split,gotcha | 2026-10-12 | 1.3/T3 | T1,T3 summary gotchas

## Research
R1.3-001 | compare vasm, clownassembler, Macroassembler AS, SN asm68k for phase 1.3 all-data baseline | 68000 assembler choice for all-data MD reassembly | assembler, vasm, clownassembler, asl, asm68k, megadrive | retriever-web | 2026-10-12 | 34 lines
R1.3-002 | compare vasm / clownassembler / AS (asl) / SN asm68k for phase 1.3 baseline and phase 1.4 instruction pinning | 68000 assembler choice for byte-matching MD disassembly | assembler, 68000, vasm, clownassembler, asl, asm68k, sha256, pinning | retriever-web | 2026-10-12 | 42 lines

## Audit
- seed: no expert runs for phase 1.3
- CLAUDE.md: 983 bytes
- .claude/skills/project-architect/SKILL.md: 13113 bytes
- .claude/skills/run-sh-one-step/SKILL.md: 798 bytes
- .claude-state/memory/MEMORY.md: 4262 bytes
- HOW_WE_WORK.md: 7000 bytes
- cookbook/INDEX.md: 1493 bytes
- rules/INDEX.md: 7032 bytes
- audit unavailable: CLI not installed (~/.claude/pa3/pa_ledger.py)

## Agent runs
- (no ledger at ~\.claude\usage-ledger\ledger.sqlite)

## Discussions
- (none)

## Deferred
- from T3: follow-up gap: make `$(OUT)` depend on generated `asm/` files (or document that `asm/` edits need `make clean`); stale no-rom.yml:19 comment; card has 0 chars headroom. (unconsumed)

## Changes
- 2026-10-12 router: T1 next -> done
- 2026-10-12 router: T2 next -> done
- 2026-10-12 router: T3 next -> done

## Plain-English Recap
Phase 1.3 made the project rebuild the game from source for the first time, with every byte still written out as plain data (an "all-data baseline": nothing is decompiled into real instructions yet). We installed an assembler, the program that turns text source into the game's binary: clownassembler v1.1.3 (`clownassembler_asm68k.exe`, 131,072 bytes, licence AGPL-3.0-or-later), fetched with the developer's approval; the exe itself is ignored by git and never tracked, and its SHA-256 fingerprint is tracked in `tools/bin/clownassembler_asm68k.exe.sha256`. A new splitter, `scripts/build/split.py`, cuts the developer's own ROM dump into 1256 ignored source files under `asm/` (all 1623 regions, 1,048,576 of 1,048,576 bytes), and the new `Makefile` reassembles them into `build/mmtt96.bin`, whose SHA-1 hash equals the original cartridge's. The first build matched with no debugging, and a second `make` does nothing except repeat the hash check.

Milestone evidence (this session, 2026-10-12): the chain `make clean && make build && make expected && cmp build/mmtt96.bin expected/mmtt96.bin && ! make build ROM=.run/absent.md && "C:/Program Files/Python311/python.exe" tools/audit_public.py` exited 0 (`.run/logs/pe13-milestone.log`): split 1623/1623 regions, 1256 files, `build/mmtt96.bin: OK`, the absent dump refused with exit 2, `audit_public: OK` with 0 offenders among 314 paths. `tools/phaseend_index.py verify` reported RED 2/3 (`.run/logs/pe13-verify.log`) only because it runs the interpreter path unquoted ("C:/Program: No such file"), so the chain was run by hand (Harness notes).

Facts established: the assembler writes a flat binary with no header or padding; a failed assert exits with code 1 and writes no output file; a 1 MiB source assembles in 0.35 s as one file and 3.9 s as 1255 includes. The fallback assembler (AS) was not needed. Gotchas: from Git bash or make the switch must be written `//p`, because a bare `/p` is rewritten into a file path; `fail` and `error` are not directives in this assembler; the exe prints no usage or version text, so the version rests on the SHA-256 alone. Four negative controls (deliberate breakages that must fail) behaved: an absent dump stops with exit 2; edits that move a region boundary are refused by the manifest and splitter, and the assembler's end-of-region assert, tested directly with a short region file, fails `init: end mismatch` with exit 2; a tampered byte gives `build/mmtt96.bin: FAILED` with exit 2; and with `config/check.*.sha` promoted to `required:` in the firewall, the public audit exits 1 when that file is moved away. The firewall holds: `asm/`, `build/` and `expected/` are ignored with 0 tracked files, and the CI workflow can only audit, since it has no dump. At close the README's build step now describes the working `make build`.

Open items: Git holds 47 local commits not yet pushed (the developer pushes; agents never do).
