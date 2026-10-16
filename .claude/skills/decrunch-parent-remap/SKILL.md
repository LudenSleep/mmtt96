---
name: decrunch-parent-remap
description: After region row inserts, remap decrunch*.tsv parent ids by start address before manifest.py
---

OBSOLETE since phase 1.7 T2: decrunch TSVs keyed by parent_start (region start hex); no remap needed.

# Decrunch Parent Remap

Captured 2026-10-13 from .run/pe16/skills.md#remap.

## When to use
after inserting or re-splitting region rows

## Steps
When: after inserting or re-splitting rows in `config/regions.retail.tsv` (manifest ids are positional and shift).
1. Before re-running `scripts/extract/manifest.py`, remap the parent ids in `config/oracle/decrunch.tsv` and
   `config/oracle/decrunch_natural.tsv` by each file's start address to the new region id holding that address.
2. Run `manifest.py`, then `manifest.py --check` (exit 0) and `make build`.
3. Note the remap as a deviation in the task log until those files are keyed by start address (1.7 follow-up).
Origin: phase 1.6/T1 summary gotcha.
