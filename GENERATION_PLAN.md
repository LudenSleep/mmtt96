# Generation 1 — Byte-identical reassembly of Micro Machines Turbo Tournament 96

Goal: a commented 68000/Z80 source tree that assembles to a ROM byte-identical to the original dump (see docs/68k-adaptation.md for how the kit ladder is adapted).
Done-criteria: a clean rebuild hash equals the original ROM SHA-1; the ROM audit and no-ROM CI are green; a fresh clone rebuilds from the maintainer's own dump by the README alone.

## Phases

<!-- Line grammar (parsed by launch.py, genend_index.py, plan_edit.py gen-close):
     - <G>.<n> <name> | milestone: … | scope: … | depends: — | status: open|closed | phase-end: phase-ends/PhaseEnd_Phase<N>.md
     Order = build order. `depends:` names phase ids or `—`. Only plan_edit.py gen-close|gen-open flips `status:`. -->

- 1.1 Extraction and manifest | milestone: one command regenerates the ROM region manifest, a second run is identical, the audit reads it as a required hash source | scope: region map, compression decoders, Z80 driver split | depends: — | status: closed | phase-end: phase-ends/PhaseEnd_Phase1.1.md
- 1.2 Oracles and load map | milestone: disassembler database round-trips from a text export; emulator oracle scripted; ROM and RAM maps proven against live memory | scope: Ghidra-class database, emulator debugger, J-Cart I/O | depends: 1.1 | status: closed | phase-end: phase-ends/PhaseEnd_Phase1.2.md
- 1.3 All-data baseline | milestone: make build emits a ROM with SHA-1 equal to the original at 100% data | scope: Makefile, split config, per-binary contract | depends: 1.2 | status: closed | phase-end: phase-ends/PhaseEnd_Phase1.3.md
- 1.4 Assembler pinned | milestone: one assembler version and flags reproduce probe routines byte-for-byte | scope: replaces compiler pinning | depends: 1.3 | status: closed | phase-end: phase-ends/PhaseEnd_Phase1.4.md
- 1.5 Census and differential harness | milestone: scanners assert coverage; a second disassembler agrees on instruction boundaries; denominators derive from the build | scope: tooling | depends: 1.4 | status: closed | phase-end: phase-ends/PhaseEnd_Phase1.5.md
- 1.6 Multipliers and encoding map | milestone: one named routine propagates to all repeats; encoding map covers each assembler form used | scope: signatures, RAM variable and struct layer, encoding map | depends: 1.5 | status: closed | phase-end: phase-ends/PhaseEnd_Phase1.6.md
- 1.7 Campaign | milestone: census reads 0 undecoded code regions; build stays hash-equal after every batch | scope: data to instructions, naming, comments | depends: 1.6 | status: closed | phase-end: phase-ends/PhaseEnd_Phase1.7.md
- 1.8 Publish gate | milestone: fresh clone rebuilds from own dump using README only; no-ROM CI green | scope: private to public flip when approved | depends: 1.7 | status: closed | phase-end: phase-ends/PhaseEnd_Phase1.8.md
- 1.9 Readability | milestone: names, comments and constants complete; build still byte-identical | scope: hardware constants, include structure | depends: 1.8 | status: closed | phase-end: phase-ends/PhaseEnd_Phase1.9.md

## Ordering rationale

- Extraction before oracles so every later phase reads one manifest; the all-data baseline before any instruction work so the byte gate exists first.
- The assembler is pinned before the campaign so conversions are provable.

## Standing constraints

- No game-derived bytes in git (ROM firewall, config/firewall.txt); the repo stays private until phase 1.8.
- The byte gate is the only proof of a match. Never push; the maintainer pushes.
- Hand-written assembly expected; if compiled C is found in phase 1.2, reinstate the kit's compiler phases.
- Later generation (not this one): browser multiplayer port.

## Changes

- 2026-10-11 developer: ladder adapted for 68000 assembly because the target is a Mega Drive game
- 2026-10-11 PhaseEnd_Phase1.1.md: phase 1.1 status -> closed
- 2026-10-12 phase-end expert: phase 1.2 status -> closed
- 2026-10-12 router: phase 1.3 status -> closed
- 2026-10-12 router: phase 1.4 status -> closed
- 2026-10-12 router: phase 1.5 status -> closed
- 2026-10-13 router: phase 1.6 status -> closed
- 2026-10-13 router: phase 1.7 status -> closed
- 2026-10-13 router: phase 1.8 status -> closed
- 2026-10-16 router: phase 1.9 status -> closed
