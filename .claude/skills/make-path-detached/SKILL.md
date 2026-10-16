---
name: make-path-detached
description: make/Java PATH, quoted interpreter, run make health and the gate detached via run.sh
---

# Make Path Detached

Captured 2026-10-13 from .run/pe/s1.md#make-path-detached.

## When to use
any make build or make health run from Bash

## Steps
- `make` lives in the WinGet ezwinports bin, not on the Bash PATH: prepend
  `export PATH="$PATH:$(ls -d ~/AppData/Local/Microsoft/WinGet/Packages/ezwinports*/bin | head -1)"`.
- Java (needed by `make build`): `C:/Program Files/Eclipse Adoptium/jdk-21.0.12.101-hotspot/bin` if not on PATH.
- The interpreter is the quoted `"C:/Program Files/Python311/python.exe"`; bare `python` is a Store install without capstone.
- `scripts/contract.sh` (and `phaseend_index.py verify`, which runs it) needs `export PY=<that interpreter>`: unset,
  it falls back to `python3` and fails `contract: FAIL ledger` (no capstone) (1.9 close).
- Run `make health` and the gate detached: `bash tools/run.sh --bg <name> -- <cmd>`, then
  `bash tools/run.sh --wait <name> --max 280`; exit code from `.run/logs/<name>.exit`.
