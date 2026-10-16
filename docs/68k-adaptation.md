# Adapting the decomp ladder to a 68000 assembly game

The kit's ladder (docs/decomp-architect.md, Part B of the intake) assumes C compiled by a pinned compiler.
Micro Machines Turbo Tournament 96 is a Mega Drive game, almost certainly hand-written 68000 (plus Z80 sound) assembly,
so this project's deliverable is a **byte-identical, readable reassembly**: commented 68000 source that an assembler
turns back into the original 1 MiB ROM. The byte gate (rebuilt ROM hash equals the original) is unchanged. Phases map as follows.

| Kit phase | Here |
|---|---|
| 0 Governance, firewall | As the kit. Done: the audit passes on the tree and fails on the planted fixture. |
| 1 Extraction + manifest | There is no filesystem. Extract = a reproducible manifest of the ROM's regions (header, vectors, code, data, compressed blobs, Z80 driver) with hashes. Find and decode any compression. |
| 2 Oracles + load map | Disassembler database (Ghidra or similar, M68000 + Z80) as a text export; an emulator with debugger/scripting as the runtime oracle. Load map = ROM banks, RAM layout, J-Cart I/O. |
| 3 All-data baseline | Every byte emitted as `dc.b` data reassembles to the identical ROM. Segment by the code/data boundaries found in Phase 2. |
| 4 Compiler pinned | **Assembler pinned**: pick the assembler and flags that reproduce the ROM (short vs long branches, absolute vs relative forms); record the exact version. Replaces compiler fingerprinting. |
| 5 Census + differential harness | Scanners assert coverage; a second disassembler must agree on instruction boundaries; progress denominators come from the build. |
| 6 Multipliers | Repeated routines and tables found by signature; the type layer becomes named RAM variables and structs from the first labeled routine. |
| 7 Codegen map + permuter | Not applicable to hand-written code. Replace with an **encoding map**: which assembler forms yield which bytes. Skip the permuter unless Phase 2 finds compiler-generated code (then reinstate Phases 4 and 7 as written). |
| 8 Campaign | Convert data to instructions routine by routine, name and comment them, keeping the byte gate green after every batch. |
| 9 Publish | The repo stays private. Phase 1.8 runs the reproducibility contract (fresh clone + own dump + README alone gives the identical ROM and green health; CI without a dump stays green). The public flip is deferred and gated on three conditions (README `## Repository visibility`): host proven free of every pushed game object (G17/DK-56), the developer's own copyright decision, the G58/G63/G64 publish conditions. |
| 10 Readability | Names, comments, include-file structure, constants for hardware registers. Reached in phase 1.9 (status below). |

**Status (phase 1.8).** Kit phases 0-5 are done here as generation phases 0.5 and 1.1-1.5: 1.4 pinned the
assembler (AS V1.42 Bld 313, `asw` + `p2bin`); 1.5 added the census, the Capstone boundary oracle and `make health`.
1.6 added routine signatures with fail-closed name propagation, the name layer (RAM/IO/struct names rendered in
listings, still byte-identical) and the encoding-form coverage scanner; it replaces kit phases 6-7.
1.7 opened kit phase 8 (campaign): every code region now builds from instruction source by default (census: 0
undecoded, checked by the health rung `ledger`); every inferred row has a recorded verdict; a first manual wave named
and commented six regions; a scripted sweep then gave every operand target and routine entry a neutral name, and the rung `commentcheck` now checks every comment's mechanical claims (names, addresses, groups, counts, coverage) against the tables. What is
left is readability (kit phase 10): comments and meaning names, in batches routed on the campaign ledger
(`config/campaign/ledger.tsv`). 1.8 (kit phase 9) keeps the repo private: it runs the reproducibility contract (bootstrap, README build, CI without a dump) and defers the public flip behind the three conditions in row 9. 1.9 completed readability (next paragraph).

**Status (phase 1.9).** Kit phase 10 (readability) is reached: every code region has a header (plate) comment, every
routine entry and named operand carries a meaning name or an `unresolved:` verdict saying what would settle it, and no
raw nameable operand remains (`scripts/census/ledger.py check --complete`); hardware constants are rendered from
`config/names/hw.tsv` (`scripts/census/constants.py check`). Every wave was gated by `scripts/census/wave_gate.sh`.
The game's behaviour, system by system with the evidence for each claim, is in `docs/mechanics.md`.

**Source location (D1, 2026-10-13).** Converted instruction source is local-only, regenerated into ignored `asm/src/` from tracked sidecars plus your own dump; never tracked: `docs/decisions/source-location.md`.

Project goal beyond the kit: once the reassembly is stable, port and modify the game for browser multiplayer. That is a
separate generation after the reassembly is readable; keep game logic separable from hardware access so a port stays feasible.
