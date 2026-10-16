# Ops index

<!-- One line per docs/ops/*.md. Edited in the same task as any tooling, path, hook or environment change. -->

## Files
- `docs/ops/ops-setup-decomp.md` — decomp environment: version pins, the game and medium, build/extract/verify, oracles, git posture, tooling inventory.
- `docs/ops/ops-tools.md` — detail behind the card's Tools rows: ghidra_db, oracle, census, signatures, names, encodings, boundaries, ledger, systems (1.9 T11), sweep, commentcheck, constants, wave_gate, health, readability checks (probe kit, wave gate, constants, completeness).

## Pins
- Assembler: AS V1.42 Bld 313 (`asw` + `p2bin`, `tools/bin/asl/`, zip sha256 in `tools/bin/asl.zip.sha256`).
- Second 68000 disassembler: Capstone 5.0.9 (wheel sha256s in `requirements-python.txt`).
- Bootstrap: `bash scripts/bootstrap.sh [--asl-zip PATH] [--dump PATH]` checks the pins, fetches + verifies AS only (detail `ops-setup-decomp.md`).
- Ghidra 12.1.4 zip: published sha256 + size in `docs/ops/ops-setup-decomp.md` (manual install).
- Emulators / db: MAME 0.289, BizHawk 2.11, Ghidra 12.1.4.

## Phase-close gate
- binding: a phase closes only on `make clean && make build && make health` green
  (`build/mmtt96.bin: OK` and `health: pairs n/n agree`, exit 0).
ops-setup-decomp.md | extract the medium and verify against the committed manifest | 155
ops-tools.md | Ops tools — detail behind the card's Tools rows | 180
