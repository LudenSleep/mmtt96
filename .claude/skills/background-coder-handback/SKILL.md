---
name: background-coder-handback
description: Coder ran in background anyway: respawn does small edits itself
---

# Background Coder Handback

Captured 2026-10-13 from .run/pe18/s1.md#background-coder-handback.

## When to use
an expert respawned after a forced hand-back

## Steps
- The Agent tool may run a coder in the background even with `run_in_background: false`; the hand-back enforcer then
  forces the expert to hand back early (1.8 tasks needed 2-4 attempts each).
- A respawned expert does small edits (one file, about 20 lines) itself instead of spawning a coder again.
- When the brief says "work directly", do the whole task in the foreground; no background agents.
- 1.9 (T14-T45, about 15 tasks): every coder spawn ran async and cost one expert respawn. Write TASK_PROGRESS.md
  before spawning a coder, and budget one attempt per coder run.
