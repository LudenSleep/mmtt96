---
name: propagate-refusal-test
description: Test propagate refusal on a header-only registry copy; a registry holding the group masks the gate
---

# Propagate Refusal Test

Captured 2026-10-13 from .run/pe16/skills.md#refusal.

## When to use
testing signatures.py propagate refusal

## Steps
When: testing that `signatures.py propagate` refuses a group when a member fails its gate.
1. Copy `config/names/routines.tsv` to `.run/` keeping only the header line.
2. Plant the member fault, run `propagate --registry <copy>`; expect refusal of the whole group, registry unchanged.
3. A registry already holding the group refuses earlier with `already in registry`, masking the gate under test.
Origin: phase 1.6/T2 summary gotcha.
