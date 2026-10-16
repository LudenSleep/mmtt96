---
name: names-edit-mirror
description: After editing config/names: db.py mirror, db.py roundtrip, pairs.py names
---

# Names Edit Mirror

Captured 2026-10-13 from .run/pe16/skills.md#names.

## When to use
after any config/names edit

## Steps
When: after any edit under `config/names/`.
1. `PY scripts/ghidra/db.py mirror` (writes `config/ghidra/{functions,symbols}.tsv`).
2. `PY scripts/ghidra/db.py roundtrip` (exit 0 iff identical).
3. `PY scripts/health/pairs.py names` (fails with unmirrored > 0 if step 1 was skipped).
4. Commit the names TSVs and the mirrored Ghidra TSVs together.
Origin: phase 1.6/T3 summary gotcha.
