MILESTONE: green

## Recap
Phase 1.3 made the project rebuild the game from source for the first time, with every byte still written out as plain data (an "all-data baseline": nothing is decompiled into real instructions yet). We installed an assembler, the program that turns text source into the game's binary: clownassembler v1.1.3 (`clownassembler_asm68k.exe`, 131,072 bytes, licence AGPL-3.0-or-later), fetched with the developer's approval; the exe itself is ignored by git and never tracked, and its SHA-256 fingerprint is tracked in `tools/bin/clownassembler_asm68k.exe.sha256`. A new splitter, `scripts/build/split.py`, cuts the developer's own ROM dump into 1256 ignored source files under `asm/` (all 1623 regions, 1,048,576 of 1,048,576 bytes), and the new `Makefile` reassembles them into `build/mmtt96.bin`, whose SHA-1 hash equals the original cartridge's. The first build matched with no debugging, and a second `make` does nothing except repeat the hash check.

Milestone evidence (this session, 2026-10-12): the chain `make clean && make build && make expected && cmp build/mmtt96.bin expected/mmtt96.bin && ! make build ROM=.run/absent.md && "C:/Program Files/Python311/python.exe" tools/audit_public.py` exited 0 (`.run/logs/pe13-milestone.log`): split 1623/1623 regions, 1256 files, `build/mmtt96.bin: OK`, the absent dump refused with exit 2, `audit_public: OK` with 0 offenders among 314 paths. `tools/phaseend_index.py verify` reported RED 2/3 (`.run/logs/pe13-verify.log`) only because it runs the interpreter path unquoted ("C:/Program: No such file"), so the chain was run by hand (Harness notes).

Facts established: the assembler writes a flat binary with no header or padding; a failed assert exits with code 1 and writes no output file; a 1 MiB source assembles in 0.35 s as one file and 3.9 s as 1255 includes. The fallback assembler (AS) was not needed. Gotchas: from Git bash or make the switch must be written `//p`, because a bare `/p` is rewritten into a file path; `fail` and `error` are not directives in this assembler; the exe prints no usage or version text, so the version rests on the SHA-256 alone. Four negative controls (deliberate breakages that must fail) behaved: an absent dump stops with exit 2; edits that move a region boundary are refused by the manifest and splitter, and the assembler's end-of-region assert, tested directly with a short region file, fails `init: end mismatch` with exit 2; a tampered byte gives `build/mmtt96.bin: FAILED` with exit 2; and with `config/check.*.sha` promoted to `required:` in the firewall, the public audit exits 1 when that file is moved away. The firewall holds: `asm/`, `build/` and `expected/` are ignored with 0 tracked files, and the CI workflow can only audit, since it has no dump. At close the README's build step now describes the working `make build`.

Open items: Git holds 47 local commits not yet pushed (the developer pushes; agents never do).

## Decisions that still bind
- Assembler pin clownassembler v1.1.3, sha256 `9d18134f…b269`, command `//p <src>,<out>`: environment fact, `docs/ops/ops-setup-decomp.md` Version pins row and card Environment Pins line.
- Boundary assert form `if * <> $END` / `inform 3,"msg"` / `endc` (rc=1, no output): contract, ops doc pins row, emitted by `split.py`, proven by T3 control 2.
- The gate is `make build` ending in `sha1sum -c config/check.retail.sha`, green = `build/mmtt96.bin: OK` and exit 0; decisive = `make clean && make build`: contract, card Build/Test lines and ops doc build section, tested by the milestone chain.
- `config/check.*.sha` is `required:` in `config/firewall.txt`: contract, tested by `tools/audit_public.py` (exit 1 when missing).
- Next task needs: make `build/mmtt96.bin` depend on the generated `asm/` files; today a hand-tampered `asm/` file is only rebuilt after deleting the bin or `make clean`.
- Next task needs: the stale comment at `.github/workflows/no-rom.yml:19` ("full-fleet compile-only run") still needs fixing.
- Next task needs: the card `HOW_WE_WORK.md` is exactly at its 7000-char cap; any addition needs a trim elsewhere.
- Next task needs: P1.2-1 stays deferred to phase 1.5.

## Harness notes
- harness: `tools/phaseend_index.py verify` runs `PY` unquoted (exit 127 / "C:/Program: No such file") and its clause splitter cuts the Milestone at a parenthetical; unfixed since 1.1; chain run by hand with a quoted interpreter.
- harness: the hand-back enforcer forces early hand-backs while a background agent runs (planner and every expert task); the first phase-1.3 planner attempt returned without a draft for that reason and was retried with foreground retrievers; T3 attempt 1 also needed a respawn.
- harness: retriever-web hit its 20-call limit and several vendor sites failed to fetch.
- harness: the assembler has no `--help`/usage (`/?` "Unrecognised switch").
- harness: GNU make (WinGet ezwinports) is not on agents' PATH by default; append its `bin` dir.
- harness: `tools/phaseend_index.py assemble 1.3` again drops the last task (T3) from `## Tasks` (same defect as 1.1, 1.2); T3 line added by hand after archive.
- harness: `phaseend_index.py assemble/archive` deleted the open `P1.2-1 deferred:1.5` row from `phase-ends/DISCUSSION_INDEX.md`; restored by hand so phase 1.5 still sees it.
- harness: `tools/commit_task.sh` does not stage `HOW_WE_WORK.md`; pass it explicitly.

## Deviations
- H7: every summary naming tools/build commands lists `HOW_WE_WORK.md` or `docs/ops/` (T1, T2, T3); no miss.
- Docs (H23): `make build` became user-visible but README step 2 still read TODO(phase-3); fixed at close by PE1.3.c1 (00d6a59).
- T3 control 2 measured the assert with a short region file because the manifest/splitter refuses regions edits first.
- Gotchas promoted: cookbook C0007 (MSYS `/x` switch rewrite), C0008 (proving a boundary assert fires). No `workflow:` gotchas; no proposed rules were pending; none ratified.
