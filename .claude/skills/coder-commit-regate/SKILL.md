---
name: coder-commit-regate
description: Re-gate rules after a dead or backgrounded coder
---

# Coder Commit Regate

Captured 2026-10-16 from .run/pe19/skills.md#coder-commit-regate.

## When to use
trusting a coder's commits before a gate

## Steps
- A coder dying on a usage limit may leave commits without a log, or nothing: re-gate HEAD before trusting its
  commits; respawn with the same brief and scratch dir (T24, T30).
- Concurrent agents building at once corrupt gate results: gate only when nothing else builds (T24).
- A progress file written while a coder runs says "do not build/gate until the coder log commit exists"; the
  respawn checks `git diff --stat <gated commit> HEAD` first (T25).
- A gated coder commit followed only by log/summary commits needs no re-gate (same diff check) (T27).
