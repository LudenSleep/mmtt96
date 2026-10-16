---
name: mame-probe-recipes
description: MAME probe recipes: contact sheet, placement, grid sweep, port taps
---

# Mame Probe Recipes

Captured 2026-10-16 from .run/pe19/skills.md#mame-probe-recipes.

## When to use
designing or reading a MAME probe run

## Steps
- Explore a new game screen: `SCEN_SNAPS=every:N`, crop/scale the run's PNGs into one contact sheet under `.run/`,
  read the sheet, then fix the input frames (T1).
- Placement probes on a race state: poke the progress-check-off word (FFD68C=1) one frame before moving the car, or
  the checkpoint ordering test takes the moved car off (T7, P049).
- Sweep a placement grid in one MAME run: a DRIVE_HOOK script reading a plan file of `frame addr bytes value` lines,
  not thousands of SCEN_POKES tokens (T8).
- J-Cart / cartridge-port evidence: Lua read/write taps on 38FFFE/380001/300000 with per-frame counts give per-run
  access bursts; probe rows cite the run ids directly (T9).
- A probe-only coder may commit probe rows without its log: read the `probes.tsv` rows' result column and the
  commits (primary artifact) before writing doc verdicts (T23, T41).
