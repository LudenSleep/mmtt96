#!/usr/bin/env bash
# wave_gate.sh — the gate of every 1.9 wave task (plan 1.9 T4): one chain, stops at the first failing step and names it.
# Steps: make build; make health; commentcheck.py (comments.tsv vs the listing); commentcheck.py --doc docs/mechanics.md;
# ledger.py check; constants.py check; asm_leak.py; audit_public.py.
# Usage: bash scripts/census/wave_gate.sh   (env PY = python with capstone, default the project pin; make on PATH)
# Prints `wave_gate: <step> ...` per step, then `wave_gate: OK` or `wave_gate: FAIL <step> (exit n)`; exit = the step's.
# Long (make health): run detached, `bash tools/run.sh --bg wave -- bash scripts/census/wave_gate.sh`.
set -u
PY="${PY:-C:/Program Files/Python311/python.exe}"
cd "$(dirname "$0")/../.." || exit 2

step() {
  local name="$1"; shift
  echo "wave_gate: $name ..."
  "$@"
  local rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "wave_gate: FAIL $name (exit $rc)"
    exit "$rc"
  fi
}

step build make build PY="$PY"
step health make health PY="$PY"
step commentcheck "$PY" scripts/census/commentcheck.py
step commentcheck-doc "$PY" scripts/census/commentcheck.py --doc docs/mechanics.md
step ledger "$PY" scripts/census/ledger.py check
step constants "$PY" scripts/census/constants.py check
step asm_leak "$PY" scripts/health/asm_leak.py
step audit_public "$PY" tools/audit_public.py
echo "wave_gate: OK"
